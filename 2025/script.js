const container = document.getElementById('shader-container');
const scene = new THREE.Scene();
const camera = new THREE.Camera();
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

const uniforms = {
    time: { value: 0 },
    resolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) }
};

const material = new THREE.ShaderMaterial({
    uniforms: uniforms,
    vertexShader: `
        void main() {
            gl_Position = vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        uniform float time;
        uniform vec2 resolution;
        
        void main() {
            vec2 uv = gl_FragCoord.xy / resolution.xy;
            vec3 color = vec3(0.0);
            
            color.r = sin(uv.x * 10.0 + time) * 0.5 + 0.5;
            color.g = cos(uv.y * 10.0 + time) * 0.5 + 0.5;
            color.b = sin(uv.x * uv.y * 20.0 + time) * 0.5 + 0.5;
            
            gl_FragColor = vec4(color, 1.0);
        }
    `
});

const geometry = new THREE.PlaneGeometry(2, 2);
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

function animate() {
    requestAnimationFrame(animate);
    uniforms.time.value += 0.01;
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    uniforms.resolution.value.set(window.innerWidth, window.innerHeight);
    renderer.setSize(window.innerWidth, window.innerHeight);
});

animate(); 