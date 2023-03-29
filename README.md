# FAR

FAR (short for Find And Replace) is an Esolang based on the simple principle that everything is a macro. Consider the following example:

    [b->k][a->e]baba

This example begins by defining the rules that 'b' is replaced by 'k', and 'a' is replaced by 'e'. Hence, the text 'baba' becomes 'keke'. Whatever text remains when the end of the file is reached is the output. Similarly:

    [ba->ke][bo->ca]baba loves boba

The output of this is 'keke loves cake'. Give it a try: `python processor.py examples/baba.far output.txt`

The remaining syntax with examples is listed in the following table.

| Key | Function | Example |
| --- | -------- | ------- |
| `+` | Denotes a variable character. | `[triple(+a)->+a+a+a]A sailor went to triple(c)` outputs `A sailor went to ccc` |
| `*` | Denotes a string. | `[I'm *S and I'm very cool->*S is full of themselves]I'm Baba and I'm very cool` outputs `Baba is full of themselves` |
| `\|` | Denotes the point that the processor should continue reading from. By default, the processor | `[baba->keke][keke->fofo]baba` outputs `fofo`, but `[baba->keke\|][keke->fofo]baba` outputs `keke` |
| `^` | Makes a rule a priority. | `[baba->keke][baba->fofo]baba` outputs `fofo`, while `[baba->keke][^baba->fofo]baba` outputs `fofo` |
| `{` and `}` | Pushes into a new scope and pops into the last scope, respectively. New rules added inside a code block will be forgotten when the block is closed. | `{[ke->ba]ke}ke` outputs `bake` |
| `<=` | Jumps to the beginning of scope (either the beginning of the code block or file). | `baba is {badbad[ba->ko][d->ol]<=}[ba->ke]<=` outputs `keke is koolkool` |

Important caveats:
- Strings take the first opportunity to terminate. Hence `[blank(*S)->]blank(func())` outputs `)`, as the string terminates on the first `)`.
- Using `|` causes all the instructions which are partially complete to reset. `[ba->|ke]` is not equivalent to `[ba->ke]` because, for example, `[ba->ke][bo->ca][cake->coffee]baba loves boba` will output `keke loves coffee`, but `[ba->|ke][bo->ca][cake->coffee]baba loves boba` outputs `keke loves cake`.
- In a future version, `{` and `}` will function as described, but currently, the code block is fixed at the time that `{` is encountered. This might not sound significant, but it prevents you from dynamically popping the scope.