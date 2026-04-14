varying vec2 vUv;

uniform float time;

// Fill these from Three.js when you hook up assets/input.
uniform sampler2D _Tex1;
uniform sampler2D _Tex2;
uniform sampler2D _mask;
uniform vec2 _mouse;
uniform vec2 resolution;

float repeat1( float v ) {
    return fract( v );
}

vec2 repeat2( vec2 v ) {
    return fract( v );
}

float sintime( float amount, float freq ) {
    return 0.5 + sin( time * freq ) * amount;
}

float sin01( float v ) {
    return 0.5 + v * 0.5;
}

float noise1D( sampler2D tex, float p ) {
    return texture2D( tex, vec2( repeat1( p ), 0.0 ) ).r;
}

float noise2D( sampler2D tex, vec2 p ) {
    return texture2D( tex, repeat2( sin(p) ) ).r;
}

// return radius, angle
vec2 polar( vec2 p ) {
    float r = length( p );
    float a = atan( p.y, p.x );
    return vec2( r, a );
}

float ymask( vec2 uv, float y, float v ) {
    return clamp( ( uv.x - y - v * 0.125 ) / v * 0.25, 0.0, 1.0 );
}

vec2 squareUv( vec2 uv ) {
    return ( uv - vec2( 0.5 ) ) * resolution / min( resolution.x, resolution.y ) + vec2( 0.5 );
}

vec2 rotateUv( vec2 uv ) {
    return vec2( 1.0 - uv.y, 1.0 - uv.x );
}

float distance_to_center( vec2 uv )
{
    return clamp(1.0 - distance( vec2( 0.5 ), uv ) * 2.0, 0.0, 1.0);
}

float planet_mask( vec2 uv ) {

    float v = 1.0;

    float radius = polar(uv - vec2(.5, .5)).x;
    float angle = polar(uv - vec2(.5,.5)).y;

    // uv += ( -vec2( 0.5 ) + vec2( 2.0 ) * sin( cos( noise2D( _Tex2, uv * 50.0 ) ) * 0.2 ) ) * 0.008;
    // uv += ( -vec2( 0.5 ) + vec2( 2.0 ) * sin( cos( noise2D( _Tex2, vec2( 0.3, 0.5 ) + uv * 3.0 ) ) * 0.2 ) ) * 0.002;
    // uv += ( -vec2( 0.5 ) + vec2( 2.0 ) * sin( cos( noise2D( _Tex2, vec2( 0.3, 0.5 ) + uv * 3.0 ) ) * 0.3 ) ) * 0.0015;

    float dtc = distance_to_center(uv);

    v = clamp( dtc, 0.0, 1.0 ) / 0.2;

    float horizon = pow (uv.y, 2.0);
    horizon *= mix( 1.0, texture2D( _mask, vec2( 0.0, dtc / 30.0 ) ).r, 0.8 );
    v *= horizon;

    return clamp(v, 0.0, 1.0);
}

vec4 clouds( vec2 uv ) {

    uv = rotateUv( uv );
    vec2 mouseUv = rotateUv( squareUv( _mouse ) );

    float v = 1.0;
    float t = time;
    float speed = 0.9;

    vec2 centeredUv = uv - vec2( 0.5 );
    vec2 polarUv = polar( centeredUv );
    float radius = polarUv.x;
    float angle = polarUv.y;
    float dtc = distance_to_center(uv);

    uv += ( -vec2( 0.5 ) + vec2( 2.0 ) * sin( cos( noise2D( _Tex2, uv * 50.0 ) ) * 0.2 ) ) * 0.008;
    uv += ( -vec2( 0.5 ) + vec2( 2.0 ) * sin( cos( noise2D( _Tex2, vec2( 0.3, 0.5 ) + uv * 3.0 ) ) * 0.2 ) ) * 0.002;
    uv += ( -vec2( 0.5 ) + vec2( 2.0 ) * sin( cos( noise2D( _Tex2, vec2( 0.3, 0.5 ) + uv * 3.0 ) ) * 0.3 ) ) * 0.0015;

    float mousedist = distance( vec2( 0.5 ), mouseUv );

    v = dtc;
    v = pow( v, 0.8 );

    float radiusclouds = polar( uv - vec2( 8.0, 0.0 ) ).x;
    v = noise2D( _mask, vec2( t * 0.002 * speed + uv.y * 0.1 + sin( angle * 0.1 ) * 0.1, radiusclouds ) );
    v *= 1.0 - v * v * v;
    v = mix( v, 1.0 - clamp( ( uv.x + radius * 0.9 - 0.01 ) / 0.95, 0.0, 1.0 ), 0.7 );

    float horizon = uv.x + sin( uv.y * 5.0 + noise1D( _mask, uv.y * 0.001 ) ) * 0.08 * noise1D( _mask, uv.y * 0.042 );
    float skymask = clamp( ( horizon - 0.39 ) / 0.001, 0.0, 1.0 );
    v = mix( v, 0.0, skymask );

    float depth = uv.y * 0.06 * clamp( ( uv.x - 0.35 ) / 0.05, 0.0, 1.0 ) + ymask( uv, 0.1, 0.08 );
    depth = repeat1( depth );

    vec3 ground = texture2D( _Tex2, vec2( repeat1( uv.x ), repeat1( t * 0.005 * speed + depth ) ) ).rgb;
    ground += sin( noise2D( _mask, vec2( uv.x * 8.0, mod( t * 0.005 * speed, 0.1 ) + depth * 14.0 ) ) ) * 0.8 * ground.r;
    ground *= 0.15;
    ground = pow( ground, vec3( 1.3 ) );

    float fog = mix( 1.0, 1.0 - clamp( ( uv.x + radius * 0.2 - 0.3 ) / 0.55, 0.0, 1.0 ), 0.75 );
    fog = fog * fog * pow( fog, 1.9 );
    ground = mix( ground, ground + vec3( fog ), 0.2 );
    ground += ground * -0.3;

    v += mix( v, ground.r, skymask );
    v *= mix( 1.0, clamp( pow( dtc, 0.1 ), 0.0, 1.0 ), texture2D( _mask, repeat2( uv ) ).r );
    v *= mix( 1.0, 0.85 + 0.15 * mousedist, step( 0.0001, length( _mouse ) ) );

    return vec4( vec3( v ), 1.0 );
}

void main() {
    vec4 c = clouds( squareUv( vUv ) );
    c += 0.2;
    c *= 0.9;
    // c = mix(c, c * planet_mask( squareUv( vUv ) ), 0.3);
    if (distance_to_center(squareUv(vUv)) < 0.05) c = vec4(1.0,1.0,1.0,0.0);
    gl_FragColor = c;
}
