import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from ReadWriteMemory import ReadWriteMemory
from struct import unpack

# Constants
WAYFARER_COLOR = 'yellow'
NICK_COLOR = 'red'

LEVELS = {
    0: {'name': '01_Chapter_Select_CS_map.webp', 'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
    1: {'name': '02_Broken_Bridge_BB_map.webp', 'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
    2: {'name': '03_Pink_Desert_PD_map.webp', 'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
    3: {'name': '04_Sunken_City_SC_map.webp', 'z': 520, 'x': 1785, 'x_step': 3.0, 'z_step': 2.985},
    4: {'name': '05_Underground_UG_map.webp', 'z': 255, 'x': 1845, 'x_step': 3.21, 'z_step': 3.2},
    5: {'name': '06_Tower_map.webp', 'z': 405, 'x': 1850, 'x_step': 3.2, 'z_step': 3.2},
    6: {'name': '07_Snow_map.webp', 'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
    7: {'name': '08_Paradise_map.webp', 'z': 780, 'x': 1660, 'x_step': 2.45, 'z_step': 2.48},
}

class JourneyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Journey")
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        self.root.state('zoomed')
        
        self.window_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        
        self.process = None
        self.image = None
        self.current_level_id = -1

        self.create_gui()
        self.connect_to_process()
        self.update()

    def create_gui(self):
        empty_image = tk.PhotoImage(width=1, height=1)
        self.img_label = tk.Label(self.root, image=empty_image)
        self.img_label.pack(fill=tk.BOTH, expand=True)
        self.root.bind("<Configure>", self.resize_canvas)

    def connect_to_process(self):
        try:
            self.rwm = ReadWriteMemory()
            self.process = self.rwm.get_process_by_name('Journey.exe')
            self.process.open()
            self.base_address = self.process.get_base_address()
            self.level_id_pointer = self.process.get_pointer(self.base_address + 0x3CFCA80, offsets=[0x70, 0x28, 0xD0, 0x100, 0x30, 0x368, 0x30])
        except Exception as e:
            print(f"Error connecting to process: {e}")
            self.root.destroy()

    def load_image(self, level_id):
        try:
            image = Image.open(LEVELS.get(self.current_level_id, {}).get('name', 'Unknown_map.webp'))
            image_resized = ImageTk.PhotoImage(image.resize((self.window_size[0], self.window_size[1]), Image.LANCZOS))
            self.img_label.config(image=image_resized)
            self.img_label.image = image_resized
            self.image = image
        except Exception as e:
            print(f"Error loading image: {e}")

    def load_dot_coordinates(self):
        wayfarer_pointer_offsets = ([0x60, 0x28, 0xD0, 0x100, 0x30, 0x370, 0xC0], [0x70, 0x28, 0xD0, 0x108, 0x30, 0x370, 0xC8])
        nick_pointer_offsets = ([0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x948], [0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x950])

        def read_coordinates(pointer, offsets):
            position = []
            address = self.base_address + pointer

            for offset in offsets:
                current_address = self.process.get_pointer(address, offsets=offset)
                position.append(unpack('<f', self.process.read(current_address).to_bytes(4, 'little'))[0])
        
            return tuple(position)

        wayfarer_position = read_coordinates(0x3C47B18, wayfarer_pointer_offsets)
        nick_position = read_coordinates(0x3C47B18, nick_pointer_offsets)

        return [wayfarer_position, nick_position]

    def draw_dots(self):
        if self.image is not None:
            image_draw = self.image.copy()
            draw = ImageDraw.Draw(image_draw)
            coordinates = self.load_dot_coordinates()

            pen_size = 8
            
            z_add = LEVELS.get(self.current_level_id, {}).get('z', 0)
            x_add = LEVELS.get(self.current_level_id, {}).get('x', 0)
            z_step = LEVELS.get(self.current_level_id, {}).get('z_step', 1.0)
            x_step = LEVELS.get(self.current_level_id, {}).get('x_step', 1.0)

            wayfarer_color = WAYFARER_COLOR
            wayfarer_x, wayfarer_z = coordinates[0]

            nick_color = NICK_COLOR
            nick_x, nick_z = coordinates[1]

            draw.ellipse((z_add + wayfarer_z * z_step - pen_size, x_add - wayfarer_x * x_step - pen_size,
                          z_add + wayfarer_z * z_step + pen_size, x_add - wayfarer_x * x_step + pen_size), fill=WAYFARER_COLOR)

            draw.ellipse((z_add + nick_z * z_step - pen_size, x_add - nick_x * x_step - pen_size,
                          z_add + nick_z * z_step + pen_size, x_add - nick_x * x_step + pen_size), fill=NICK_COLOR)

            image_resized = ImageTk.PhotoImage(image_draw.resize((self.window_size[0], self.window_size[1]), Image.LANCZOS))
            self.img_label.config(image=image_resized)
            self.img_label.image = image_resized

    def resize_canvas(self, event):
        width = event.width
        height = event.height

        if (width, height) != self.window_size:
            self.window_size = (width, height)

    def update(self):
        new_level_id = self.process.read(self.level_id_pointer)
        if new_level_id != self.current_level_id:
            self.current_level_id = new_level_id
            self.load_image(self.current_level_id)

        self.draw_dots()
        self.root.after(500, self.update)

    def run(self):
        self.root.mainloop()

    def close(self):
        if self.process:
            self.process.close()

if __name__ == "__main__":
    app = JourneyApp()
    app.run()
    app.close()
