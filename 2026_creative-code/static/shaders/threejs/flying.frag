varying vec2 vUv;

uniform float time;
uniform sampler2D _Tex1;
uniform sampler2D _Tex2;
uniform sampler2D _mask;
uniform vec2 _mouse;
uniform vec2 resolution;

#define CAM_POS vec3( 0.0, 2.8, 0.0 )
#define FOV 120.0

mat3 cam( vec3 pos, vec3 target ) {
    vec3 f = normalize( target - pos );
    vec3 r = normalize( cross( f, vec3( 0.0, 1.0, 0.0 ) ) );
    vec3 u = cross( r, f );
    return mat3( r, u, f );
}

void main() {
    vec2 fragCoord = vUv * resolution;
    vec2 uv = ( fragCoord - 0.5 * resolution ) / resolution.y;

    float focal = 1.0 / tan( radians( FOV ) * 0.5 );
    vec3 rd = normalize( cam( CAM_POS, CAM_POS + vec3( 0.0, 0.0, 1.0 ) ) * vec3( uv, focal ) );
    vec2 wc = vec2( 0.0, time * 40.0 );

    vec4 color;
    float t = -CAM_POS.y / rd.y;

    if ( t > 0.0 ) {
        vec3 p = CAM_POS + t * rd;
        vec2 tc = p.xz * 0.5 + 0.5;
        color = texture2D( _Tex1, ( tc + wc ) * 0.004 );
    } else {
        t = ( -CAM_POS.y + 50.0 ) / rd.y;
        vec3 p = CAM_POS + t * rd;
        vec2 tc = p.xz * 0.5 + 0.5;
        color = texture2D( _Tex2, ( tc + wc * 5.0 ) * 0.0001 );

        float x = fract( rd.x );
        float y = 1.0 - clamp( rd.y * 3.0, 0.0, 1.0 );
        color.rgb += vec3( 1.0 ) * y * 0.6;

        x = fract( rd.x );
        y = 1.0 - clamp( rd.y + 0.04, 0.0, 1.0 );
        vec4 fc = texture2D( _mask, vec2( x, y * 1.1 ) );
        vec3 hc = texture2D( _Tex1, vec2( 0.5 + x * 0.001, y * 0.01 ) ).rgb + 0.4;
        float a = clamp( fc.r - 0.1 - ( 1.0 - y ) * 9.0, 0.0, 1.0 );
        a = pow( a, 1.0 / 50.0 );
        color.rgb = mix( color.rgb, hc * pow( fc.r, 1.0 / 10.0 ), a );
    }

    color.a = 1.0;
    gl_FragColor = color;
}
