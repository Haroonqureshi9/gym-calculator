#!/usr/bin/env python3
# ^ "Shebang" line. On Mac/Linux it tells the OS to run this file with python3
#   if you execute it directly (./file.py). On Windows it's ignored. Harmless either way.

"""
Workout Tracker Suite - Day 1: Barbell Plate Calculator
Visual plate calculator with Tkinter GUI showing optimal plate loading.
"""
# ^ A module docstring (triple-quoted string at the top of the file). It's just
#   documentation describing what the file does. It runs as a "statement" but has no effect.

import tkinter as tk
# ^ Import the standard GUI library. "as tk" lets us type tk.Button instead of tkinter.Button.
from tkinter import ttk, messagebox
# ^ Pull two specific things out of tkinter: ttk (nicer "themed" widgets) and
#   messagebox (for popup dialogs like errors and info boxes).
import json
# ^ Import json, used to save/load saved lifts to a text file in JSON format.
from pathlib import Path
# ^ Import the Path class, a modern way to handle file paths (instead of raw strings).


# Plate colors (standard gym colors)
PLATE_COLORS_LBS = {
# ^ A dictionary mapping a plate's weight (in lbs) -> a color (hex string).
#   Used later to color the plates when drawing them.
    45: '#FF0000',   # Red       <- key 45 maps to red
    35: '#FFD700',   # Yellow/Gold
    25: '#00FF00',   # Green
    10: '#FFFFFF',   # White
    5: '#0000FF',    # Blue
    2.5: '#FF4444',  # Small red
}
# ^ Closing brace of the dictionary.

PLATE_COLORS_KG = {
# ^ Same idea but for kilogram plates (different weights, different color convention).
    25: '#FF0000',   # Red
    20: '#0000FF',   # Blue
    15: '#FFD700',   # Yellow
    10: '#00FF00',   # Green
    5: '#FFFFFF',    # White
    2.5: '#FF4444',  # Small red
    1.25: '#4444FF', # Small blue
}

# Plate dimensions (width, height)
PLATE_SIZES_LBS = {
# ^ Maps plate weight -> a (width, height) tuple in pixels, so bigger plates draw bigger.
    45: (25, 90),    # 45 lb plate drawn 25px wide, 90px tall
    35: (22, 80),
    25: (19, 70),
    10: (16, 55),
    5: (13, 45),
    2.5: (10, 35),
}

PLATE_SIZES_KG = {
# ^ Same drawing dimensions but keyed by kg plate weights.
    25: (25, 90),
    20: (22, 80),
    15: (19, 70),
    10: (16, 55),
    5: (13, 45),
    2.5: (10, 35),
    1.25: (8, 30),
}

# Available plates
PLATES_LBS = [45, 35, 25, 10, 5, 2.5]
# ^ A plain list of the plate denominations available in lbs. The calculator
#   only uses these sizes when figuring out what to load.
PLATES_KG = [25, 20, 15, 10, 5, 2.5, 1.25]
# ^ Same, for kg.

# Bar weights
BARS = {
# ^ Dictionary of selectable bars. Key = the label shown in the dropdown.
#   Value = a tuple (weight_in_lbs, weight_in_kg) for that bar.
    'Standard Olympic (45 lbs / 20 kg)': (45, 20),
    'Women\'s Olympic (35 lbs / 15 kg)': (35, 15),
    # ^ The \' is an escaped apostrophe so it doesn't end the string early.
    'Training Bar (15 lbs / 7 kg)': (15, 7),
}


class PlateCalculator:
# ^ Define a class. A class bundles data (attributes) and behavior (methods) together.
#   This one class IS the whole app.
    """Barbell plate calculator GUI"""
    # ^ Class docstring describing the class.

    def __init__(self, root):
    # ^ The constructor. Runs automatically when you do PlateCalculator(root).
    #   "self" is the object being created; "root" is the main window passed in.
        self.root = root
        # ^ Store the window on the object so other methods can use it via self.root.
        self.root.title("🏋️ Barbell Plate Calculator")
        # ^ Set the text in the window's title bar.
        self.root.geometry("900x700")
        # ^ Set the window size to 900px wide by 700px tall.
        self.root.resizable(False, False)
        # ^ Disallow resizing in both width (False) and height (False).

        # State
        self.unit = 'lbs'
        # ^ Current unit. Starts in pounds.
        self.bar_weight = 45
        # ^ Current bar weight. Starts at 45 (lbs).
        self.saved_lifts_file = Path('saved_lifts.json')
        # ^ The file where saved lifts are stored. Path object pointing at that filename.

        # Create UI
        self.create_widgets()
        # ^ Call our own method to build all the buttons, labels, canvas, etc.

        # Initial calculation
        self.calculate_plates()
        # ^ Run one calculation immediately so the app isn't blank on startup.

    def create_widgets(self):
    # ^ Method that builds every visual element. Called once from __init__.
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        # ^ A Frame is an invisible container that holds other widgets. 10px padding inside.
        main_frame.pack(fill=tk.BOTH, expand=True)
        # ^ .pack() places the frame in the window. fill=BOTH means stretch in both
        #   directions; expand=True means take up extra space.

        # Title
        title = tk.Label(
            main_frame,                       # parent = the main frame
            text="🏋️ BARBELL PLATE CALCULATOR", # the text shown
            font=('Arial', 20, 'bold')        # font family, size, weight
        )
        title.pack(pady=10)
        # ^ Place the title; pady=10 adds 10px of vertical space above and below.

        # Input section
        input_frame = ttk.Frame(main_frame)
        # ^ Another container, this one for the row of inputs.
        input_frame.pack(fill=tk.X, pady=10)
        # ^ fill=X = stretch horizontally only.

        # Target weight input
        tk.Label(input_frame, text="Target Weight:", font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        # ^ Make a label and immediately pack it. side=LEFT puts it on the left of the row.
        #   padx=5 = 5px horizontal spacing. (We don't store this label; we never change it.)

        self.weight_var = tk.StringVar(value="225")
        # ^ A StringVar is a special tkinter variable tied to a widget. It holds the text
        #   typed in the entry box. Starts as "225". Stored on self so other methods can read/set it.
        weight_entry = tk.Entry(input_frame, textvariable=self.weight_var, width=10, font=('Arial', 14))
        # ^ A text input box. textvariable links it to weight_var (they stay in sync).
        weight_entry.pack(side=tk.LEFT, padx=5)
        # ^ Place it.
        weight_entry.bind('<KeyRelease>', lambda e: self.calculate_plates())
        # ^ "bind" = run code on an event. <KeyRelease> fires every time a key is let go,
        #   so the calculation re-runs as you type. lambda e: ... is a tiny throwaway
        #   function; "e" is the event object (we ignore it).

        # Unit selector
        self.unit_var = tk.StringVar(value="lbs")
        # ^ Variable holding which radio button is selected ("lbs" or "kg").
        unit_lbs = tk.Radiobutton(input_frame, text="lbs", variable=self.unit_var, value="lbs",
                                   command=self.toggle_unit)
        # ^ A radio button. All radios sharing the same "variable" act as one group.
        #   When clicked it sets unit_var to "lbs" and calls toggle_unit.
        unit_lbs.pack(side=tk.LEFT, padx=5)
        unit_kg = tk.Radiobutton(input_frame, text="kg", variable=self.unit_var, value="kg",
                                  command=self.toggle_unit)
        # ^ The "kg" radio in the same group.
        unit_kg.pack(side=tk.LEFT, padx=5)

        # Bar selector
        tk.Label(input_frame, text="Bar:", font=('Arial', 12)).pack(side=tk.LEFT, padx=(20, 5))
        # ^ Label for the bar dropdown. padx=(20, 5) = 20px left, 5px right.
        self.bar_var = tk.StringVar(value='Standard Olympic (45 lbs / 20 kg)')
        # ^ Variable holding the currently selected bar's label. Default = standard Olympic bar.
        bar_dropdown = ttk.Combobox(input_frame, textvariable=self.bar_var, width=30, state='readonly')
        # ^ A Combobox = dropdown menu. state='readonly' means the user must pick from the
        #   list and can't type their own value.
        bar_dropdown['values'] = list(BARS.keys())
        # ^ Fill the dropdown's options with the keys of the BARS dictionary (the bar labels).
        bar_dropdown.pack(side=tk.LEFT, padx=5)
        bar_dropdown.bind('<<ComboboxSelected>>', lambda e: self.update_bar())
        # ^ When a new option is chosen, call update_bar.

        # Quick presets
        preset_frame = ttk.Frame(main_frame)
        # ^ Container for the preset buttons row.
        preset_frame.pack(fill=tk.X, pady=10)

        tk.Label(preset_frame, text="Quick Presets:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        # ^ Label before the preset buttons.

        presets_lbs = [135, 185, 225, 315, 405]
        # ^ Common barbell milestones in lbs (135 = bar + two 45s, etc.).
        for weight in presets_lbs:
        # ^ Loop over each preset weight to make a button for it.
            btn = tk.Button(preset_frame, text=str(weight), width=6,
                          command=lambda w=weight: self.load_preset(w))
            # ^ Make a button labeled with the weight. The "w=weight" trick captures the
            #   current loop value; without it, every button would use the last weight.
            btn.pack(side=tk.LEFT, padx=3)
            # ^ Place each button to the left.

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        # ^ A thin horizontal line for visual separation.

        # Canvas for barbell visualization
        self.canvas = tk.Canvas(main_frame, width=850, height=200, bg='white', relief=tk.SUNKEN, bd=2)
        # ^ A Canvas is a blank drawing surface. We'll draw the bar and plates on it.
        #   bg=white background, relief=SUNKEN + bd=2 give it an inset border look.
        self.canvas.pack(pady=10)
        # ^ Place the canvas. Stored on self because draw_barbell needs to draw on it later.

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Results section
        results_frame = ttk.Frame(main_frame)
        # ^ Container for the text results.
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Plates list
        tk.Label(results_frame, text="PLATES PER SIDE:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        # ^ Heading label. anchor=W aligns it to the West (left) edge.

        self.plates_text = tk.Text(results_frame, height=6, width=50, font=('Arial', 11), state=tk.DISABLED)
        # ^ A multi-line Text box that lists the plates. state=DISABLED makes it read-only
        #   (we temporarily enable it in code when we want to update its contents).
        self.plates_text.pack(fill=tk.X, pady=5)

        # Total info
        self.total_label = tk.Label(results_frame, text="", font=('Arial', 11, 'bold'))
        # ^ A label that will show the total weight summary. Starts empty; filled in later.
        self.total_label.pack(pady=5)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Saved lifts section
        saved_frame = ttk.Frame(main_frame)
        saved_frame.pack(fill=tk.X)

        tk.Label(saved_frame, text="SAVED LIFTS:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        # ^ Heading for the saved-lifts area.

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        # ^ Container for the action buttons.
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Save Current Lift", command=self.save_lift, bg='#4CAF50', fg='white',
                 font=('Arial', 10, 'bold'), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        # ^ Green "Save" button. bg=background color, fg=text color. Calls save_lift when clicked.
        tk.Button(btn_frame, text="Load Saved", command=self.load_saved_lifts, bg='#2196F3', fg='white',
                 font=('Arial', 10, 'bold'), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        # ^ Blue "Load" button -> load_saved_lifts.
        tk.Button(btn_frame, text="Clear", command=self.clear, bg='#f44336', fg='white',
                 font=('Arial', 10, 'bold'), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        # ^ Red "Clear" button -> clear.

    def toggle_unit(self):
    # ^ Called when a unit radio button is clicked.
        self.unit = self.unit_var.get()
        # ^ Read the selected unit ("lbs" or "kg") from the variable and store it.
        self.update_bar()
        # ^ Recompute the bar weight for the new unit.
        self.calculate_plates()
        # ^ Recalculate plates for the new unit.

    def update_bar(self):
    # ^ Updates bar_weight based on the chosen bar and current unit.
        bar_name = self.bar_var.get()
        # ^ Get the selected bar's label.
        bar_lbs, bar_kg = BARS[bar_name]
        # ^ Look it up in BARS and unpack the (lbs, kg) tuple into two variables.
        self.bar_weight = bar_lbs if self.unit == 'lbs' else bar_kg
        # ^ Pick the lbs value if unit is lbs, otherwise the kg value (a "ternary" expression).
        self.calculate_plates()
        # ^ Recalculate now that the bar weight changed.

    def load_preset(self, weight):
    # ^ Called by a preset button; "weight" is that button's number.
        self.weight_var.set(str(weight))
        # ^ Put the preset number into the entry box (as text).
        self.calculate_plates()
        # ^ Recalculate.

    def calculate_plates(self):
    # ^ The core math: figure out which plates to load.
        try:
            target = float(self.weight_var.get())
            # ^ Read the typed weight and convert it to a number.
        except ValueError:
            return
            # ^ If the box has non-numeric text (e.g. empty or "abc"), float() throws
            #   ValueError; we just stop quietly so it doesn't crash.

        if target <= self.bar_weight:
        # ^ If the goal weight is at or below the bare bar, no plates are needed.
            self.display_results([], target)
            # ^ Show an empty plate list.
            return
            # ^ Stop here.

        # Get available plates
        plates = PLATES_LBS if self.unit == 'lbs' else PLATES_KG
        # ^ Choose the right list of plate sizes for the current unit.

        # Round to nearest achievable weight
        smallest_increment = min(plates) * 2
        # ^ The smallest change you can make to total bar weight = smallest plate x 2
        #   (because a plate goes on BOTH sides).
        target = round(target / smallest_increment) * smallest_increment
        # ^ Snap the target to the nearest multiple of that increment, so the result
        #   is actually loadable with real plates.

        # Calculate plates needed per side
        weight_per_side = (target - self.bar_weight) / 2
        # ^ Subtract the bar, then halve, because plates are split across both sides.

        # Greedy algorithm
        plates_needed = []
        # ^ Will hold tuples like (plate_weight, count).
        remaining = weight_per_side
        # ^ How much weight we still need to cover on one side.

        for plate in sorted(plates, reverse=True):
        # ^ Go through plates from heaviest to lightest.
            count = int(remaining / plate)
            # ^ How many of THIS plate fit into the remaining weight (whole number).
            if count > 0:
            # ^ Only record it if at least one fits.
                plates_needed.append((plate, count))
                # ^ Save the plate and how many.
                remaining -= plate * count
                # ^ Subtract the weight those plates account for, then move to the next size.

        self.display_results(plates_needed, target)
        # ^ Hand the result off to be drawn and listed.

    def display_results(self, plates_needed, total_weight):
    # ^ Updates the canvas, the text list, and the totals label.
        # Draw barbell
        self.draw_barbell(plates_needed)
        # ^ Draw the visual bar with these plates.

        # Update plates list
        self.plates_text.config(state=tk.NORMAL)
        # ^ Temporarily make the read-only text box editable so we can change it.
        self.plates_text.delete(1.0, tk.END)
        # ^ Clear everything. "1.0" means line 1, character 0; END means the end.

        if not plates_needed:
        # ^ If the list is empty...
            self.plates_text.insert(tk.END, "Empty bar only!\n")
            # ^ ...just say so.
        else:
            for plate, count in plates_needed:
            # ^ Otherwise list each plate type.
                color_name = self.get_color_name(plate)
                # ^ Get a human-readable color for this plate.
                self.plates_text.insert(tk.END, f"• {count} × {plate} {self.unit} ({color_name})\n")
                # ^ Add a line like "• 2 × 45 lbs (Red)". f"..." is an f-string that inserts
                #   the variables in {} into the text.

        self.plates_text.config(state=tk.DISABLED)
        # ^ Lock the text box again so the user can't edit it.

        # Update total
        other_unit = 'kg' if self.unit == 'lbs' else 'lbs'
        # ^ The opposite unit, for showing a conversion.
        converted = self.convert_weight(total_weight)
        # ^ Convert the total into that other unit.

        weight_per_side = (total_weight - self.bar_weight) / 2
        # ^ Recompute per-side weight for display.

        self.total_label.config(
            text=f"Total: {total_weight} {self.unit} ({converted} {other_unit})\n"
                 f"Each side: {weight_per_side} {self.unit} ({self.bar_weight} {self.unit} bar + {weight_per_side * 2} {self.unit} plates)"
        )
        # ^ Build a two-line summary string and put it in the label. The two f-strings sitting
        #   next to each other are automatically joined into one string.

    def draw_barbell(self, plates_needed):
    # ^ Draws the bar and plates onto the canvas.
        self.canvas.delete('all')
        # ^ Wipe the canvas clean before redrawing.

        # Bar dimensions
        bar_length = 600       # how long the bar line is, in pixels
        bar_x_start = 125      # x-coordinate where the bar starts (left end)
        bar_y = 100            # y-coordinate (vertical center) of the bar
        bar_width = 15         # thickness of the bar line

        # Draw bar
        self.canvas.create_line(
            bar_x_start, bar_y,                 # start point (x, y)
            bar_x_start + bar_length, bar_y,    # end point (x, y)
            fill='#888888', width=bar_width     # gray, 15px thick
        )
        # ^ Draws the horizontal bar.

        # Draw center grip
        grip_width = 150
        # ^ Width of the knurled grip section in the middle.
        grip_x = bar_x_start + (bar_length - grip_width) / 2
        # ^ X position so the grip is centered on the bar.
        self.canvas.create_rectangle(
            grip_x, bar_y - 20,                 # top-left corner
            grip_x + grip_width, bar_y + 20,    # bottom-right corner
            fill='#666666', outline='black', width=2
        )
        # ^ A darker rectangle representing the grip.
        self.canvas.create_text(
            grip_x + grip_width / 2, bar_y,     # centered on the grip
            text="GRIP", font=('Arial', 10, 'bold'), fill='white'
        )
        # ^ The word "GRIP" written on the grip.

        if not plates_needed:
        # ^ If there are no plates, we're done after drawing the bare bar.
            return

        # Get plate colors and sizes
        colors = PLATE_COLORS_LBS if self.unit == 'lbs' else PLATE_COLORS_KG
        # ^ Pick the right color table for the current unit.
        sizes = PLATE_SIZES_LBS if self.unit == 'lbs' else PLATE_SIZES_KG
        # ^ Pick the right size table.

        # Draw plates on left side
        x_offset = bar_x_start - 10
        # ^ Start drawing just inside the left end of the bar. As we add plates we'll
        #   move LEFT (decreasing x).
        for plate_weight, count in plates_needed:
        # ^ For each plate type and how many of it...
            for _ in range(count):
            # ^ ...repeat "count" times. "_" means we don't care about the loop number.
                color = colors.get(plate_weight, '#CCCCCC')
                # ^ Look up the plate's color; gray (#CCCCCC) as a fallback if missing.
                width, height = sizes.get(plate_weight, (10, 30))
                # ^ Look up the plate's drawing size; (10, 30) as fallback.

                # Draw plate
                self.canvas.create_rectangle(
                    x_offset - width, bar_y - height/2,   # top-left
                    x_offset, bar_y + height/2,           # bottom-right
                    fill=color, outline='black', width=2
                )
                # ^ Draw the plate as a colored rectangle, centered vertically on the bar.

                # Label
                self.canvas.create_text(
                    x_offset - width/2, bar_y - height/2 - 15,  # just above the plate
                    text=str(plate_weight), font=('Arial', 9, 'bold')
                )
                # ^ Write the plate's number above it.

                x_offset -= width + 3
                # ^ Move left by the plate's width plus a 3px gap, ready for the next plate.

        # Draw plates on right side (mirror)
        x_offset = bar_x_start + bar_length + 10
        # ^ Start just outside the right end of the bar. This time we move RIGHT.
        for plate_weight, count in plates_needed:
            for _ in range(count):
                color = colors.get(plate_weight, '#CCCCCC')
                width, height = sizes.get(plate_weight, (10, 30))

                # Draw plate
                self.canvas.create_rectangle(
                    x_offset, bar_y - height/2,           # top-left
                    x_offset + width, bar_y + height/2,   # bottom-right
                    fill=color, outline='black', width=2
                )
                # ^ Same as the left side but drawn to the right of x_offset.

                # Label
                self.canvas.create_text(
                    x_offset + width/2, bar_y - height/2 - 15,
                    text=str(plate_weight), font=('Arial', 9, 'bold')
                )

                x_offset += width + 3
                # ^ Move right for the next plate.

    def get_color_name(self, plate_weight):
    # ^ Turns a plate weight into a readable color name for the text list.
        colors_lbs = {45: 'Red', 35: 'Yellow', 25: 'Green', 10: 'White', 5: 'Blue', 2.5: 'Small Red'}
        # ^ Name lookup for lbs plates.
        colors_kg = {25: 'Red', 20: 'Blue', 15: 'Yellow', 10: 'Green', 5: 'White', 2.5: 'Small Red', 1.25: 'Small Blue'}
        # ^ Name lookup for kg plates.

        colors = colors_lbs if self.unit == 'lbs' else colors_kg
        # ^ Pick the right table.
        return colors.get(plate_weight, 'Gray')
        # ^ Return the name, or 'Gray' if the weight isn't in the table.

    def convert_weight(self, weight):
    # ^ Converts a weight to the OTHER unit.
        if self.unit == 'lbs':
            return round(weight * 0.453592, 1)
            # ^ lbs -> kg (1 lb = 0.453592 kg), rounded to 1 decimal place.
        else:
            return round(weight * 2.20462, 1)
            # ^ kg -> lbs (1 kg = 2.20462 lb), rounded to 1 decimal.

    def save_lift(self):
    # ^ Saves the current weight under a name the user types.
        try:
            weight = float(self.weight_var.get())
            # ^ Read and validate the current weight.
        except ValueError:
            messagebox.showerror("Error", "Invalid weight")
            # ^ Show an error popup if the weight isn't a number.
            return

        # Ask for name
        dialog = tk.Toplevel(self.root)
        # ^ Toplevel = a new separate window (a popup) on top of the main one.
        dialog.title("Save Lift")
        dialog.geometry("300x120")

        tk.Label(dialog, text="Lift Name:", font=('Arial', 11)).pack(pady=10)
        # ^ Prompt label in the popup.

        name_var = tk.StringVar()
        # ^ Variable to hold the typed name.
        entry = tk.Entry(dialog, textvariable=name_var, width=25, font=('Arial', 11))
        # ^ Text box for the name.
        entry.pack(pady=5)
        entry.focus()
        # ^ Put the cursor in this box automatically so the user can type right away.

        def save():
        # ^ A nested function (defined inside save_lift). Runs when the popup's Save is clicked.
            name = name_var.get().strip()
            # ^ Read the typed name, removing leading/trailing spaces.
            if not name:
            # ^ If empty after stripping...
                messagebox.showerror("Error", "Please enter a name")
                return
                # ^ ...complain and stop.

            # Load existing
            lifts = {}
            # ^ Start with an empty dictionary in case the file doesn't exist.
            if self.saved_lifts_file.exists():
            # ^ If we already have a save file...
                with open(self.saved_lifts_file, 'r') as f:
                # ^ Open it for reading. "with" auto-closes the file afterward.
                    lifts = json.load(f)
                    # ^ Parse the JSON in the file into a Python dictionary.

            # Save
            lifts[name] = {'weight': weight, 'unit': self.unit}
            # ^ Add/overwrite this lift in the dictionary.

            with open(self.saved_lifts_file, 'w') as f:
            # ^ Open the file for writing (overwrites it).
                json.dump(lifts, f, indent=2)
                # ^ Write the dictionary back out as JSON, indented for readability.

            dialog.destroy()
            # ^ Close the popup.
            messagebox.showinfo("Success", f"Saved {name}: {weight} {self.unit}")
            # ^ Confirmation popup.

        tk.Button(dialog, text="Save", command=save, bg='#4CAF50', fg='white',
                 font=('Arial', 10, 'bold'), padx=20, pady=5).pack(pady=10)
        # ^ The popup's Save button, wired to the nested save() function above.

    def load_saved_lifts(self):
    # ^ Shows saved lifts and lets the user load one.
        if not self.saved_lifts_file.exists():
        # ^ No file yet means nothing to load.
            messagebox.showinfo("Info", "No saved lifts found")
            return

        with open(self.saved_lifts_file, 'r') as f:
            lifts = json.load(f)
            # ^ Read the saved lifts into a dictionary.

        if not lifts:
        # ^ File exists but is empty.
            messagebox.showinfo("Info", "No saved lifts found")
            return

        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        # ^ New popup window.
        dialog.title("Load Saved Lift")
        dialog.geometry("350x300")

        tk.Label(dialog, text="Select a lift:", font=('Arial', 12, 'bold')).pack(pady=10)

        listbox = tk.Listbox(dialog, font=('Arial', 11), height=10)
        # ^ A Listbox shows a scrollable list of selectable items.
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for name, data in lifts.items():
        # ^ Loop over each saved lift (name + its data).
            listbox.insert(tk.END, f"{name}: {data['weight']} {data['unit']}")
            # ^ Add a readable line for each one to the list.

        def load():
        # ^ Nested function run when the popup's Load button is clicked.
            selection = listbox.curselection()
            # ^ Which item is highlighted (returns a tuple of indices).
            if not selection:
            # ^ Nothing selected -> do nothing.
                return

            name = list(lifts.keys())[selection[0]]
            # ^ Turn the dict keys into a list and pick the one at the selected index.
            data = lifts[name]
            # ^ Get that lift's stored data.

            self.weight_var.set(str(data['weight']))
            # ^ Put its weight into the main entry box.
            self.unit_var.set(data['unit'])
            # ^ Set the unit radio button to match.
            self.toggle_unit()
            # ^ Apply the unit change (which also recalculates).

            dialog.destroy()
            # ^ Close the popup.

        tk.Button(dialog, text="Load", command=load, bg='#2196F3', fg='white',
                 font=('Arial', 10, 'bold'), padx=20, pady=5).pack(pady=10)
        # ^ The popup's Load button.

    def clear(self):
    # ^ Resets the calculator to a bare bar.
        self.weight_var.set("45")
        # ^ Set the weight box back to 45.
        self.calculate_plates()
        # ^ Recalculate (will show an empty bar since 45 <= bar weight in lbs).


def main():
# ^ The entry point that starts the whole app.
    root = tk.Tk()
    # ^ Create the main application window.
    app = PlateCalculator(root)
    # ^ Build our calculator inside that window. This triggers __init__.
    root.mainloop()
    # ^ Start the event loop: this keeps the window open and responds to clicks/typing.
    #   The program "sits" here until you close the window.


if __name__ == "__main__":
# ^ True only when this file is run directly (not imported by another file).
    main()
    # ^ Kick everything off.