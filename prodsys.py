import tkinter as tk


class Fact:
    iid: str
    desc: str
    is_atom: bool

    def __init__(self, _id: str, desc: str):
        self.iid = _id
        self.desc = desc
        self.is_atom = False

    def __repr__(self) -> str:
        return self.desc

    @staticmethod
    def parse(data: str) -> 'Fact':
        # print(data)
        try:
            _id, desc, _ = map(str.strip, data.split(';'))
            return Fact(_id, desc)
        except ValueError as e:
            raise ValueError(f'Invalid fact: {data}') from e

    def __hash__(self) -> int:
        return hash(self.desc)


class Rule:
    iid: str
    desc: str
    lhs: set[str]
    rhs: set[str]

    def __init__(self, _id: str, desc: str, lhs: set[str], rhs: set[str]):
        self.iid = _id
        self.desc = desc
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self) -> str:
        return self.desc

    @staticmethod
    def parse(data: str) -> 'Rule':
        # print(data)
        try:
            _id, lhs, rhs, _, desc = map(str.strip, data.split(';'))
            lhs = set(map(str.strip, lhs.split(',')))
            rhs = set(map(str.strip, rhs.split(',')))
            return Rule(_id, desc, lhs, rhs)
        except ValueError as e:
            raise ValueError(f'Invalid rule: {data}') from e

    def __hash__(self) -> int:
        return hash(self.desc)

    @property
    def reverse_desc(self):
        return ' -> '.join(self.desc.split(' -> ')[::-1])


class App(tk.Tk):
    facts: list[Fact]
    rules: list[Rule]

    def __init__(self):
        super().__init__()
        self.title('Production System')
        self.minsize(1000, 400)
        self.geometry('1000x400')
        self.facts = []
        self.rules = []
        self.load_facts()
        self.load_rules()
        self.set_atoms()
        self.create_widgets()
        self.targets.insert(tk.END, *self.facts)
        self.inventory.insert(tk.END, *self.facts)
        self.reset()
        self.bind('<Escape>', self.reset)
        self.state('zoomed')

    def create_widgets(self):
        self.frame1 = tk.Frame(self)
        self.frame2 = tk.Frame(self)
        self.inventory = tk.Listbox(self.frame1, width=40, height=20, selectmode=tk.MULTIPLE, exportselection=False)
        self.targets = tk.Listbox(self.frame1, width=40, height=20, selectmode=tk.MULTIPLE, exportselection=False)
        self.scroll1 = tk.Scrollbar(self.frame1, orient=tk.VERTICAL, command=self.inventory.yview)
        self.scroll2 = tk.Scrollbar(self.frame1, orient=tk.VERTICAL, command=self.targets.yview)
        self.status = tk.Text(self.frame1, width=40, height=20, state=tk.DISABLED)
        self.label1 = tk.Label(self.frame1, text='Инвентарь\n->')
        self.label2 = tk.Label(self.frame1, text='Сделать\n->')
        self.directb = tk.Button(self.frame2, text='Прямой Вывод', command=self.direct)
        self.reverseb = tk.Button(self.frame2, text='Обратный Вывод', command=self.reverse)

        self.frame1.pack(side='top', padx=10, pady=10, fill='both', expand=True)
        self.frame2.pack(side='bottom', padx=10, pady=10)
        self.label1.pack(side='left')
        self.inventory.pack(side='left', fill='both')
        self.scroll1.pack(side='left', fill='y')
        self.label2.pack(side='left')
        self.targets.pack(side='left', fill='both')
        self.scroll2.pack(side='left', fill='y')
        self.status.pack(side='left', fill='both', expand=True)
        self.directb.pack(side='left', padx=1)
        self.reverseb.pack(side='left', padx=1)
        self.inventory.config(yscrollcommand=self.scroll1.set)
        self.targets.config(yscrollcommand=self.scroll2.set)

    def load_facts(self, path: str = 'facts.txt'):
        with open(path, encoding='utf8') as f:
            for line in f:
                if line and not line.startswith('\n'):
                    self.facts.append(Fact.parse(line))
        self.facts.sort(key=str)

    def load_rules(self, path: str = 'rules.txt'):
        with open(path, encoding='utf8') as f:
            for line in f:
                if line and not line.startswith('\n'):
                    self.rules.append(Rule.parse(line))

    def set_atoms(self):
        for fact in self.facts:
            if not any(fact.iid in rule.rhs for rule in self.rules):
                fact.is_atom = True
                # print(fact)

    def _open_status(self):
        self.status.configure(state=tk.NORMAL)

    def _close_status(self):
        self.status.configure(state=tk.DISABLED)

    def _clear_status(self):
        self._open_status()
        self.status.delete(1.0, tk.END)
        self._close_status()

    def reset(self, *_):
        self._open_status()
        self.status.delete(1.0, tk.END)
        self.status.insert(tk.END, 'Выберите факты и нажмите кнопку')
        self._close_status()
        self.targets.selection_clear(0, tk.END)
        self.inventory.selection_clear(0, tk.END)

    def direct(self):
        facts = {self.facts[i].iid for i in self.inventory.curselection()}
        target = self.facts[self.targets.curselection()[0]].iid
        prev_step = facts.copy()
        cur_step = facts.copy()
        self._clear_status()
        self._open_status()

        while True:
            for rule in self.rules:
                if rule.lhs.issubset(prev_step) and not rule.rhs.issubset(cur_step):
                    cur_step.update(rule.rhs)
                    self.status.insert(tk.END, f'{rule}\n')
                    if target in cur_step:
                        self.status.insert(tk.END, 'Цель достигнута')
                        self._close_status()
                        return
            if cur_step == prev_step:
                break
            prev_step = cur_step.copy()
        if target not in cur_step:
            self.status.insert(tk.END, 'Цель не достигнута')
        self._close_status()

    def reverse(self):
        facts = {self.facts[i] for i in self.targets.curselection()}
        all_facts = {fact.iid: fact for fact in self.facts}
        s: list[Fact] = []
        for fact in facts:
            s.append(fact)

        self._clear_status()
        self._open_status()

        while s:
            fact = s.pop()
            if fact.is_atom:
                self.status.insert(tk.END, f'{fact}\n')
            else:
                for rule in self.rules:
                    if fact.iid in rule.rhs:
                        self.status.insert(tk.END, f'{rule.reverse_desc}\n')
                        # print(rule.reverse_desc)
                        for lhs in rule.lhs:
                            s.append(all_facts[lhs])

    def run(self):
        self.mainloop()


if __name__ == '__main__':
    app = App()
    app.run()
