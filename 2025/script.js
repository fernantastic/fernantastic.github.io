const container = document.getElementById('shader-container');
const scene = new THREE.Scene();
const camera = new THREE.Camera();
const renderer = new THREE.WebGLRenderer({
    antialias: false,
    powerPreference: 'low-power',
    precision: 'lowp'
});

function updateSize() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const pixelRatio = Math.min(window.devicePixelRatio, 2);
    
    uniforms.resolution.value.set(width, height);
    renderer.setSize(width, height, false);
    renderer.setPixelRatio(pixelRatio);
}

renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
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
            vec2 uv = (gl_FragCoord.xy - resolution.xy) / min(resolution.x, resolution.y);
            vec3 color = vec3(1.0);
            
            float circle = 1.0 - smoothstep(0.8, 1.5, length(uv));
            color *= circle * -1.0;

            color.r += sin(uv.x * 15.0 + time * 2.0) * 0.5 + 0.5;
            color.g += cos(uv.y * 5.0 + time * 2.0) * 0.5 + 0.5;
            color.b += sin(uv.x * 10.0 + time * 2.0) * 0.5 + 0.5;
            
            gl_FragColor = vec4(color, 1.0);
        }
    `
});

const geometry = new THREE.PlaneGeometry(2, 2);
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

let lastTime = 0;
const targetFPS = 30;
const frameInterval = 1000 / targetFPS;

function animate(currentTime) {
    requestAnimationFrame(animate);
    
    const deltaTime = currentTime - lastTime;
    if (deltaTime < frameInterval) return;
    
    lastTime = currentTime - (deltaTime % frameInterval);
    uniforms.time.value += 0.01;
    renderer.render(scene, camera);
}

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(updateSize, 50);
});

window.addEventListener('orientationchange', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(updateSize, 500);
});

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        lastTime = performance.now();
    }
});

updateSize();
animate(performance.now()); 