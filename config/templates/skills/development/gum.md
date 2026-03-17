---
name: gum
description: bash scripting, bash TUI, linux TUI, bash menu, bash coding, linux scripting, TUI coding
---

### CRITICAL: Gum `--selected` Rules

1. **NO COMMAS in item strings** - Gum uses commas as separator for `--selected`
   - BAD: `network|net-tools|Network utilities (ifconfig, etc)|`
   - GOOD: `network|net-tools|Network utilities (ifconfig etc)|`

2. **Comma-separated string, NOT multiple flags**
   - BAD: `--selected "item1" --selected "item2"`
   - GOOD: `--selected "item1,item2"`

3. **Items must match EXACTLY** - including suffixes like `[installed]`
   - If display shows `pkg - description [installed]`, preselected must be identical

4. **Empty selection = cancel** - Always check `[ -z "$selected" ] && return`
   - Pressing Esc returns empty string
   - NEVER interpret empty as "remove all" - that's destructive

### Gum Syntax

```bash
# Height - use space, not equals
--height 25        # CORRECT
--height=25        # WRONG

# Multi-select with pre-selection
local preselected_str="item1,item2,item3"
selected=$(printf '%s\n' "${items[@]}" | gum choose --no-limit \
    --cursor.foreground 212 \
    --height 25 \
    --header "Space=toggle, Enter=confirm" \
    --selected "$preselected_str")

# ALWAYS handle cancel (Esc)
[ -z "$selected" ] && return
```

### Known Gum Issues

- "nothing selected" message on Esc - comes from gum itself (GitHub issue #877), cannot be suppressed
- `--selected` is `[]string` type in Kong CLI library - expects comma-separated values
