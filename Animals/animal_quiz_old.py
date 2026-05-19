import tkinter as tk
import random

# ================== NÁZVY ZVÍŘAT A SOUBORŮ ==================

ANIMALS = {
    "Elephant": "elephant.png",
    "Lion": "lion.png",
    "Horse": "horse.png",
    "Monkey": "monkey.png",
    "Giraffe": "giraffe.png",
    "Zebra": "zebra.png",
    "Snake": "snake.png",
    "Tortoise": "tortoise.png",
    "Brown Bear": "bear.png",
    "Rhinoceros": "rhinoceros (rhino).png",
    "Camel": "camel.png",
    "Bald Eagle": "eagle.png",
    "Red Fox": "fox.png",
    "Wolf": "wolf.png",
    "Pig": "pig.png",
    "Goat": "goat.png",
    "Cow": "cow.png",
    "Goose": "goose.png",
    "Duck": "duck.png",
    "Turkey": "turkey.png",
    "Deer": "deer.png",
    "Sheep": "sheep.png",
    "Parrot": "parrot.png",
    "Hippopotamus": "hippopotamus (hippo).png"
}


class AnimalQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Animal Quiz")
        self.root.configure(bg="white")
        # pevná velikost, ať to není přes celou obrazovku
        self.root.geometry("900x700")

        # stav
        self.current_animal = None
        self.correct_button_index = None
        self.images = {}
        self.blink_job = None
        self.blink_state = False

        # načtení obrázků
        self.load_images()

        # horní zpráva
        self.message_label = tk.Label(
            root, text="", font=("Helvetica", 20, "bold"), bg="white"
        )
        self.message_label.pack(pady=10)

        # obrázek zvířete
        self.image_label = tk.Label(root, bg="white")
        self.image_label.pack(pady=10)

        # rám pro tlačítka
        btn_frame = tk.Frame(root, bg="white")
        btn_frame.pack(pady=20)

        # tlačítko New animal
        self.new_button = tk.Button(
            btn_frame,
            text="New animal",
            font=("Helvetica", 14),
            command=self.new_animal
        )
        self.new_button.grid(row=0, column=0, columnspan=4, pady=10)

        # čtyři tlačítka s názvy zvířat
        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(
                btn_frame,
                text="",
                width=18,
                font=("Helvetica", 14),
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.grid(row=1, column=i, padx=10, pady=10)
            self.answer_buttons.append(btn)

        # první zvíře
        self.new_animal()

    def load_images(self):
        """Načte obrázky do self.images podle ANIMALS."""
        for name, filename in ANIMALS.items():
            try:
                img = tk.PhotoImage(file=filename)
            except Exception as e:
                print(f"Chyba při načítání {filename}: {e}")
                img = None
            self.images[name] = img

    def reset_message(self):
        """Zruší blikání a smaže zprávu."""
        if self.blink_job is not None:
            self.root.after_cancel(self.blink_job)
            self.blink_job = None
        self.message_label.config(text="", fg="black")
        self.blink_state = False

    def start_blinking(self):
        """Rozbliká nápis Excellent!!!."""
        self.blink_state = not self.blink_state

        if self.blink_state:
            self.message_label.config(fg="green")
        else:
            self.message_label.config(fg=self.root.cget("bg"))

        self.blink_job = self.root.after(500, self.start_blinking)

    def new_animal(self):
        """Vybere nové zvíře a nastaví tlačítka."""
        self.reset_message()

        animal_names = list(ANIMALS.keys())
        if len(animal_names) < 4:
            raise ValueError("Potřebuješ alespoň 4 zvířata v ANIMALS.")

        self.current_animal = random.choice(animal_names)

        img = self.images[self.current_animal]
        if img is None:
            # když není obrázek, zobrazíme alespoň text
            self.image_label.config(
                text=self.current_animal,
                image="",
                font=("Helvetica", 32, "bold")
            )
        else:
            self.image_label.config(image=img, text="")
            self.image_label.image = img  # držet referenci

        other = [name for name in animal_names if name != self.current_animal]
        wrong_options = random.sample(other, 3)

        options = wrong_options + [self.current_animal]
        random.shuffle(options)

        self.correct_button_index = options.index(self.current_animal)

        for i, name in enumerate(options):
            self.answer_buttons[i].config(text=name)

    def check_answer(self, index):
        """Reakce na kliknutí na tlačítko s názvem zvířete."""
        if self.current_animal is None:
            return

        if index == self.correct_button_index:
            if self.blink_job is not None:
                self.root.after_cancel(self.blink_job)
                self.blink_job = None

            self.message_label.config(text="Excellent!!!")
            self.start_blinking()
        else:
            if self.blink_job is not None:
                self.root.after_cancel(self.blink_job)
                self.blink_job = None
            self.message_label.config(text="Wrong, try again...", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimalQuizApp(root)
    root.mainloop()
