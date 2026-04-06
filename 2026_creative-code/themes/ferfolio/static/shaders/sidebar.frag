precision mediump float;

varying vec2 v_uv;
uniform float u_time;

vec3 tanh_approx(vec3 x) {
  vec3 a = exp(x);
  vec3 b = exp(-x);
  return (a - b) / (a + b);
}

void main() {
  vec2 uv = v_uv;
  vec3 c = vec3(0,0,0);
  for(int i = 0; i < 36; i++)
  {
    c.x += uv.x ;
    c.y += sin(uv.y + u_time * 0.2) * 0.8;
    c.z += cos(uv.x + .4 + u_time * 0.3) * .6;
    
  }
  c = tanh_approx(c * c / 4e2);
  //uv.x = mod(uv.x + u_time * 0.15, 1.0);
  //vec3 color = vec3(uv.x, uv.y, 0.5 + 0.5 * sin(uv.x * 12.0));
  gl_FragColor = vec4(c, 1.0);
}
