// Get the canvas element
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Set the canvas dimensions
canvas.width = 400;
canvas.height = 400;

// Define the snake and food objects
let snake = [
    {x: 200, y: 200},
    {x: 190, y: 200},
    {x: 180, y: 200},
    {x: 170, y: 200},
    {x: 160, y: 200}
];

let food = {x: Math.floor(Math.random() * 40) * 10, y: Math.floor(Math.random() * 40) * 10};

// Define the direction and score variables
let direction = 'RIGHT';
let score = 0;

// Draw the snake and food on the canvas
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < snake.length; i++) {
        ctx.fillStyle = 'green';
        ctx.fillRect(snake[i].x, snake[i].y, 10, 10);
    }
    ctx.fillStyle = 'red';
    ctx.fillRect(food.x, food.y, 10, 10);
    ctx.fillStyle = 'black';
    ctx.font = '24px Arial';
    ctx.fillText(`Score: ${score}`, 10, 24);
}

// Update the snake position and check for collisions
function update() {
    let head = {x: snake[0].x, y: snake[0].y};
    if (direction === 'RIGHT') {
        head.x += 10;
    } else if (direction === 'LEFT') {
        head.x -= 10;
    } else if (direction === 'UP') {
        head.y -= 10;
    } else if (direction === 'DOWN') {
        head.y += 10;
    }
    snake.unshift(head);
    if (snake[0].x === food.x && snake[0].y === food.y) {
        score++;
        food = {x: Math.floor(Math.random() * 40) * 10, y: Math.floor(Math.random() * 40) * 10};
    } else {
        snake.pop();
    }
    if (snake[0].x < 0 || snake[0].x >= canvas.width || snake[0].y < 0 || snake[0].y >= canvas.height || checkCollision()) {
        alert(`Game Over! Your score is ${score}.`);
        snake = [
            {x: 200, y: 200},
            {x: 190, y: 200},
            {x: 180, y: 200},
            {x: 170, y: 200},
            {x: 160, y: 200}
        ];
        food = {x: Math.floor(Math.random() * 40) * 10, y: Math.floor(Math.random() * 40) * 10};
        direction = 'RIGHT';
        score = 0;
    }
}

// Check for collision with the snake's body
function checkCollision() {
    for (let i = 1; i < snake.length; i++) {
        if (snake[0].x === snake[i].x && snake[0].y === snake[i].y) {
            return true;
        }
    }
    return false;
}

// Handle keyboard input
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' && direction !== 'LEFT') {
        direction = 'RIGHT';
    } else if (e.key === 'ArrowLeft' && direction !== 'RIGHT') {
        direction = 'LEFT';
    } else if (e.key === 'ArrowUp' && direction !== 'DOWN') {
        direction = 'UP';
    } else if (e.key === 'ArrowDown' && direction !== 'UP') {
        direction = 'DOWN';
    }
});

// Main game loop
setInterval(() => {
    update();
    draw();
}, 100);
