import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from ReadWriteMemory import ReadWriteMemory
from struct import unpack

def load_image(level_id):
    global image, img_label, window_size
    image = Image.open(f"level_0{level_id}.webp")
    image_resized = ImageTk.PhotoImage(image.resize((window_size[0], window_size[1]), Image.LANCZOS))
    img_label.config(image=image_resized)
    img_label.image = image_resized

def load_dot_coordinates():
    global wayfarer_pointers, nick_pointers
    
    wayfarer_position = (unpack('<f', process.read(wayfarer_pointers[0]).to_bytes(4, 'little'))[0], 
                    unpack('<f', process.read(wayfarer_pointers[1]).to_bytes(4, 'little'))[0])
    nick_position = (unpack('<f', process.read(nick_pointers[0]).to_bytes(4, 'little'))[0], 
                    unpack('<f', process.read(nick_pointers[1]).to_bytes(4, 'little'))[0])

    return [wayfarer_position, nick_position]
    

def draw_dots():
    global image, img_label, window_size, current_level_id
    
    if image:
        image_draw = image.copy()
        draw = ImageDraw.Draw(image_draw)
        coordinates = load_dot_coordinates()

        pen_size = 8
        
        level_adds = {
            0: {'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
            1: {'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
            2: {'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
            3: {'z': 520, 'x': 1785, 'x_step': 3.0, 'z_step': 2.985},
            4: {'z': 255, 'x': 1845, 'x_step': 3.21, 'z_step': 3.2},
            5: {'z': 405, 'x': 1850, 'x_step': 3.2, 'z_step': 3.2},
            6: {'z': 410, 'x': 1840, 'x_step': 3.2, 'z_step': 3.2},
            7: {'z': 780, 'x': 1660, 'x_step': 2.45, 'z_step': 2.48},
        }

        
        z_add = level_adds[current_level_id]['z']
        x_add = level_adds[current_level_id]['x']

        z_step = level_adds[current_level_id]['z_step']
        x_step = level_adds[current_level_id]['x_step']

        wayfarer_color = 'yellow'
        wayfarer_x, wayfarer_z = coordinates[0]

        nick_color = 'red'
        nick_x, nick_z = coordinates[1]

        draw.ellipse((z_add + wayfarer_z * z_step - pen_size, x_add - wayfarer_x * x_step - pen_size, z_add + wayfarer_z * z_step + pen_size, x_add - wayfarer_x * x_step + pen_size), fill=wayfarer_color)
        draw.ellipse((z_add + nick_z * z_step - pen_size, x_add - nick_x * x_step - pen_size, z_add + nick_z * z_step + pen_size, x_add - nick_x * x_step + pen_size), fill=nick_color)

        image_resized = ImageTk.PhotoImage(image_draw.resize((window_size[0], window_size[1]), Image.LANCZOS))
        img_label.config(image=image_resized)
        img_label.image = image_resized

def resize_canvas(event):
    global window_size

    width = event.width
    height = event.height

    if (width, height) != window_size:
        window_size = (width, height)


def update():
    global current_level_id, level_id_pointer

    new_level_id = process.read(level_id_pointer)
    if new_level_id != current_level_id:
        current_level_id = new_level_id
        load_image(current_level_id)

    draw_dots()
    root.after(1000, update)



rwm = ReadWriteMemory()
process = rwm.get_process_by_name('Journey.exe')
process.open()
base_address = process.get_base_address()
level_id_pointer = process.get_pointer(base_address + 0x3CFCA80, offsets=[0x70, 0x28, 0xD0, 0x100, 0x30, 0x368, 0x30])
wayfarer_pointers = (process.get_pointer(base_address + 0x3C47B18, offsets=[0x60, 0x28, 0xD0, 0x100, 0x30, 0x370, 0xC0]),
                    process.get_pointer(base_address + 0x3C47B18, offsets=[0x70, 0x28, 0xD0, 0x108, 0x30, 0x370, 0xC8]))

nick_pointers = (process.get_pointer(base_address + 0x3C47B18, offsets=[0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x948]),
                process.get_pointer(base_address + 0x3C47B18, offsets=[0x60, 0x28, 0xD0, 0x108, 0x4A0, 0x10, 0x950]))

root = tk.Tk()
root.title("Journey")

window_size = (root.winfo_screenwidth(), root.winfo_screenheight())
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
root.state('zoomed')

empty_image = tk.PhotoImage(width=1, height=1)

img_label = tk.Label(root, image=empty_image)
img_label.pack(fill=tk.BOTH, expand=True)

current_level_id = -1
image = None

root.bind("<Configure>", resize_canvas)

update()

root.mainloop()
process.close()
