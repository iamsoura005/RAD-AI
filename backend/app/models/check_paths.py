import os

# Check where __file__ resolves in model_loader location
this_dir = os.path.dirname(os.path.abspath(__file__))
print("model_loader dir:", this_dir)

# Walk up the tree
for i in range(5):
    p = os.path.abspath(os.path.join(this_dir, *[".."] * i))
    h5_present = any(f.endswith('.h5') for f in os.listdir(p) if os.path.isfile(os.path.join(p, f)))
    print(f"  {'../' * i or './'} -> {p}  [has .h5: {h5_present}]")
    if h5_present:
        print("    Files:", [f for f in os.listdir(p) if f.endswith('.h5')])
