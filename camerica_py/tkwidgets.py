from tkinter import *
import tkinter
from tkinter import simpledialog

# mostly ripped off from the _QueryDialog in simpledialog
class _QueryList(simpledialog.Dialog):
    def __init__(self, title, prompt, choices, selected=None):
        # display a list chooser with the given title and prompt
        # choices an iterable of strings to put in the list,
        # and selected is the index of the one to show first

        self.prompt = prompt
        self.choices = choices
        self.selected = selected
        
        self.cancelled = True

        simpledialog.Dialog.__init__(self, tkinter._default_root, title)

    def destroy(self):
        self.entry = None
        simpledialog.Dialog.destroy(self)

    def body(self, master):
        w = Label(master, text=self.prompt, justify=LEFT)
        w.grid(row=0, padx=5, sticky=W)

        self.entry = Listbox(master, name="entry")
        self.entry.grid(row=1, padx=5, sticky=W+E)
        
        for choice in self.choices:
            self.entry.insert(END, choice)
        
        if self.selected is not None:
            self.entry.activate(self.selected)
        
        return self.entry

    def validate(self):
        self.selected = self.entry.index(ACTIVE)

        return 1
        
    def cancel(self, event=None):
        if self.cancelled:
            self.selected = None
            self.withdraw()
            self.update_idletasks()
            
        super().cancel(event)
    
    def apply(self):
        self.cancelled = False
        
def asklist(title, prompt, choices, selected=None):
    d = _QueryList(title, prompt, choices, selected)
    return d.selected