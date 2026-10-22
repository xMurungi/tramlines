# Chapter 2 — Hello, world

> Somewhere in this book, a brain of 138,639 neurons will wake up on your computer. It starts here, with one line.

## Where we are
You know where files live and how to open a [terminal](glossary.md). This chapter installs Python and runs the first program you have ever written.

## The idea
A computer does nothing on its own. It follows instructions, exactly and only. A [program](glossary.md) is a list of those instructions, written in a language precise enough that there is no room for guessing.

Think of a recipe written for a cook who has never seen a kitchen and will do *exactly* what the page says, nothing more. If the recipe says "add salt" and does not say how much, this cook stops. Python is the language we write our recipes in. The "cook" is a program called the Python interpreter, which reads your recipe line by line and carries it out.

The tradition, since the 1970s, is that the first program anyone writes in a new language prints *Hello, world*. We will keep it.

## Build it

1. **Install uv.** [uv](glossary.md) is the tool that installs Python for you and keeps each project's tools separate. On macOS or Linux, paste this into the terminal and press Enter:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    On Windows, open PowerShell and run:

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    Close the terminal and open a new one, so it notices the new tool.

2. **Install Python 3.12.**

    ```bash
    uv python install 3.12
    ```

3. **Make a folder for this chapter and go into it.**

    ```bash
    mkdir -p tramlines-book/ch02
    cd tramlines-book/ch02
    ```

4. **Write the program.** Open a text editor, make a new file, and type this single line exactly:

    ```python
    print("Hello, world.")
    ```

    Save it as `hello.py` inside the `ch02` folder.

## Run it

```bash
uv run --python 3.12 python hello.py
```

You should see:

```text
Hello, world.
```

## The click
You just gave a machine an instruction and it obeyed, exactly. `print` is the name of an instruction Python already knows: "show this on the screen". The parentheses hand it something to show. The quotation marks tell Python that `Hello, world.` is text to be shown as-is, not more instructions.

Here is the part that matters for the rest of this book. Run it again. And again. It prints the same thing every time, letter for letter. That is not luck; it is what computers *are*. Given the same instructions and the same starting point, a computer does the same thing. Much later, we will give the computer a whole fly brain, and this same property will let us build a copy that sees its future. The machine in this book is built on the line you just typed.

## Break it
Change one thing, predict what will happen, then run it.

1. Remove the closing quotation mark: `print("Hello, world.)`. What does Python say?
2. Write `Print` with a capital P. Does Python care about capital letters?
3. Add a second line, `print("I am about to build a brain.")`. In what order do the lines appear?
4. Put your own name in place of `world`.

## When it goes wrong

- **`command not found: uv`.** The terminal was opened before uv was installed. Close it, open a new one, and try again.
- **`SyntaxError: unterminated string literal`.** A quotation mark is missing. Every opening `"` needs a closing `"`.
- **`can't open file 'hello.py'`.** You are in a different folder from the file. Run `ls` (macOS/Linux) or `dir` (Windows) to see what is here, and `cd` into the folder that holds `hello.py`.

## Check yourself

1. What is a program?
2. What does `print` do?
3. Why does `Hello, world.` need quotation marks?
4. If you run `hello.py` a thousand times, how many different outputs will you see?

??? note "Answers"
    1. A list of instructions, written in a language a computer can follow exactly.
    2. It shows the value you give it on the screen.
    3. The quotation marks mark it as text to show, rather than instructions for Python to carry out.
    4. One. Same instructions, same start, same result. Remember this; it comes back in Chapter 12, and again at the heart of the machine.

## Decisions in this chapter

- [ADR-0004: Python 3.12](../decisions/0004-python-and-pytorch.md)
- [ADR-0012: uv and the rest of the toolbox](../decisions/0012-development-tooling.md)

## Next
Your program said one fixed thing; in Chapter 3 you will teach it to remember things, and that is where a neuron's voltage will live.
