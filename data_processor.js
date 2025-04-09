class Maze {
    constructor(width, height) {
        this.width = width;
        this.height = height;
        this.grid = Array.from({ length: height }, () => Array(width).fill("#"));
        this.visited = new Set();
        this.directions = [
            [0, -1], // Left
            [0, 1],  // Right
            [-1, 0], // Up
            [1, 0],  // Down
        ];
    }

    shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    isValid(x, y) {
        return x >= 0 && y >= 0 && x < this.height && y < this.width;
    }

    generate(x, y) {
        this.grid[x][y] = " ";
        this.visited.add(`${x},${y}`);

        this.shuffle(this.directions);

        for (const [dx, dy] of this.directions) {
            const nx = x + dx * 2;
            const ny = y + dy * 2;

            if (this.isValid(nx, ny) && !this.visited.has(`${nx},${ny}`)) {
                this.grid[x + dx][y + dy] = " ";
                this.generate(nx, ny);
            }
        }
    }

    printMaze() {
        console.log(this.grid.map(row => row.join("")).join("\n"));
    }

    createMaze() {
        this.generate(1, 1);
        this.grid[1][0] = "S"; // Start
        this.grid[this.height - 2][this.width - 1] = "E"; // End
    }
}

const width = 21; // Odd number for proper walls
const height = 21;

const maze = new Maze(width, height);
maze.createMaze();
maze.printMaze();
