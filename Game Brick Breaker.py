import tkinter as tk


class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        coords = self.canvas.coords(self.item)
        if len(coords) > 4:  # Jika item adalah poligon
            x_coords = coords[::2]  # Ambil nilai x
            y_coords = coords[1::2]  # Ambil nilai y
            return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
        return coords

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 5

        points = [
            x, y - self.radius,
            x - self.radius, y,
            x - self.radius / 2, y + self.radius,
            x, y + self.radius / 2,
            x + self.radius / 2, y + self.radius,
            x + self.radius, y
        ]
        item = canvas.create_polygon(
            points,
            fill='#FF69B4',
            outline='#C71585'
        )
        super().__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Bounce off the walls
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1

        # Move the ball
        self.move(self.direction[0] * self.speed, self.direction[1] * self.speed)

    def collide(self, objects):
        for obj in objects:
            if isinstance(obj, Paddle):
                self.direction[1] *= -1
            elif isinstance(obj, Brick):
                obj.hit()
                self.direction[1] *= -1


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 100
        self.height = 20
        self.ball = None
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill='#FFC0CB', outline='#FF69B4'
        )
        super().__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if 0 <= coords[0] + offset and coords[2] + offset <= width:
            super().move(offset, 0)
            if self.ball:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 50
        self.hits = hits
        color = Brick.COLORS[hits]
        points = [
            x, y - self.height / 4,
            x - self.width / 4, y - self.height / 2,
            x - self.width / 2, y,
            x, y + self.height / 2,
            x + self.width / 2, y,
            x + self.width / 4, y - self.height / 2,
        ]
        item = canvas.create_polygon(points, fill=color, outline='black', tags='brick')
        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.lives = 3
        self.running = True
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(
            self, bg='#FFD1DC', width=self.width, height=self.height
        )
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 370)
        self.items[self.paddle.item] = self.paddle
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 90, 2)
            self.add_brick(x + 37.5, 130, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-20))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(20))

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(self.width / 2, self.height / 2, 'Press Space to Spread Love!', 25)
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) / 2
        self.ball = Ball(self.canvas, x, 350)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size=20):
        font = ('Comic Sans MS', size)
        return self.canvas.create_text(x, y, text=text, font=font, fill='black')

    def update_lives_text(self):
        text = f'Lives: {self.lives}'
        if not self.hud:
            self.hud = self.draw_text(70, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.running = True
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.set_ball(None)
        self.game_loop()

    def game_loop(self):
        if not self.running:
            return
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.running = False
            self.draw_text(self.width / 2, self.height / 2, 'You Spread Love Everywhere!', 30)
        elif self.ball.get_position()[3] >= self.height:
            self.lives -= 1
            if self.lives < 0:
                self.running = False
                self.draw_text(self.width / 2, self.height / 2, 'Love is Eternal!', 30)
            else:
                self.setup_game()
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)  # Menggunakan bounding box
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Spread Love')
    game = Game(root)
    game.mainloop()
