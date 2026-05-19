import tkinter as tk
import random
import subprocess
from pathlib import Path
import time

SCRIPT_DIR = Path(__file__).resolve().parent

def speak_english(text: str):
    """
    Přečte nahlas anglický text pomocí macOS příkazu 'say'.
    """
    try:
        subprocess.run(["say", "-v", "Samantha", text])
    except Exception as e:
        print("TTS error:", e)

# Malý testovací seznam zvířat
ANIMALS = {
    "Elephant": "elephant.png",
    "Lion": "lion.png",
    "Horse": "horse.png",
    "Monkey": "monkey.png",
    "Giraffe": "giraffe.png",
    "Zebra": "zebra.png",
    "Snake": "snake.png",
    "Tortoise": "tortoise.png",
    "Bear": "bear.png",
    "Rhinoceros": "rhinoceros (rhino).png",
    "Camel": "camel.png",
    "Eagle": "eagle.png",
    "Fox": "fox.png",
    "Wolf": "wolf.png",
    "Pig": "pig.png",
    "Goat": "goat.png",
    "Cow": "cow.png",
    "Goose": "goose.png",
    "Duck": "duck.png",
    "Turkey": "turkey.png",
    "Rabbit": "rabbit.png",
    "Mouse": "mouse.png",
    "Deer": "deer.png",
    "Sheep": "sheep.png",
    "Parrot": "parrot.png",
    "Hippopotamus": "hippopotamus (hippo).png",
    "Dog": "dog.png",
    "Cat": "cat.png",
    "Fish": "fish.png"
}


class AnimalQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Animal Quiz")
        self.root.configure(bg="white")
        self.root.geometry("800x600")  # pevné menší okno

        self.current_animal = None
        self.correct_button_index = None
        self.images = {}
        self.blink_job = None
        self.blink_state = False
        self.remaining_animals = []

        # horní text
        self.message_label = tk.Label(
            root, text="Choose the correct animal name:",
            font=("Helvetica", 28, "bold"), bg="white"
        )
        self.message_label.pack(pady=10)

        self.status_label = tk.Label(
            root, text="", font=("Helvetica", 12), bg="white", fg="gray"
        )
        self.status_label.pack(pady=(0, 5))

        # obrázek
        self.image_label = tk.Label(root, bg="white")
        self.image_label.pack(pady=10)

        self.load_images()

        # rámeček pro tlačítka
        btn_frame = tk.Frame(root, bg="white")
        btn_frame.pack(pady=20)

        # New animal
        self.new_button = tk.Button(
            btn_frame,
            text="New animal",
            font=("Helvetica", 36),
            command=self.new_animal
        )
        self.new_button.grid(row=0, column=0, columnspan=4, pady=10)

        # 4 odpovědi
        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(
                btn_frame,
                text="",
                width=10,
                font=("Helvetica", 36),
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.grid(row=1, column=i, padx=10, pady=10)
            self.answer_buttons.append(btn)

        self.new_animal()

    def load_images(self):
        """Načte obrázky a zmenší je, aby nebyly přes celou obrazovku."""
        t0 = time.perf_counter()
        loaded = 0
        for name, filename in ANIMALS.items():
            try:
                img = tk.PhotoImage(file=str(SCRIPT_DIR / filename))
                # zmenšíme obrázek, pokud je příliš velký
                w = img.width()
                h = img.height()
                max_size = 350  # max šířka/výška v okně

                scale = max(w / max_size, h / max_size, 1)
                # použijeme integer subsample, aby to prošlo
                scale_int = int(scale)
                if scale_int > 1:
                    img = img.subsample(scale_int, scale_int)

            except Exception as e:
                print(f"Chyba při načítání {filename}: {e}")
                img = None
            if img is not None:
                loaded += 1
            self.images[name] = img
        dt = time.perf_counter() - t0
        msg = f"Images: {loaded}/{len(ANIMALS)} | {dt:.3f}s | {SCRIPT_DIR}"
        print(f"Image load: dir={SCRIPT_DIR}, ok={loaded}/{len(ANIMALS)}, time={dt:.3f}s")
        self.status_label.config(text=msg)

    def reset_message(self):
        if self.blink_job is not None:
            self.root.after_cancel(self.blink_job)
            self.blink_job = None
        self.message_label.config(text="Choose the correct animal name:", fg="black")
        self.blink_state = False

    def start_blinking(self):
        self.blink_state = not self.blink_state

        if self.blink_state:
            self.message_label.config(text="Excellent!!!", fg="green")
        else:
            self.message_label.config(text="", fg="green")

        self.blink_job = self.root.after(400, self.start_blinking)

    def new_animal(self):
        self.reset_message()

        animal_names = list(ANIMALS.keys())
        if len(animal_names) < 4:
            raise ValueError("Potřebuješ alespoň 4 zvířata v ANIMALS.")

        if not self.remaining_animals:
            self.remaining_animals = list(animal_names)
            random.shuffle(self.remaining_animals)
        self.current_animal = self.remaining_animals.pop()

        img = self.images[self.current_animal]
        if img is None:
            self.image_label.config(
                text=self.current_animal,
                image="",
                font=("Helvetica", 32, "bold")
            )
        else:
            self.image_label.config(image=img, text="")
            self.image_label.image = img  # udržení reference

        other = [name for name in animal_names if name != self.current_animal]
        wrong_options = random.sample(other, 3)

        options = wrong_options + [self.current_animal]
        random.shuffle(options)

        self.correct_button_index = options.index(self.current_animal)

        for i, name in enumerate(options):
            self.answer_buttons[i].config(text=name)

    def check_answer(self, index):
        if self.current_animal is None:
            return

        if index == self.correct_button_index:
            if self.blink_job is not None:
                self.root.after_cancel(self.blink_job)
                self.blink_job = None
            self.start_blinking()
            speak_english(self.current_animal)
        else:
            if self.blink_job is not None:
                self.root.after_cancel(self.blink_job)
                self.blink_job = None
            self.message_label.config(text="Wrong, try again...", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimalQuizApp(root)
    root.mainloop()
