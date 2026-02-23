def fibonacci(n):
    """Vrací n-tý člen Fibonacciho posloupnosti."""
    if n <= 0:
        raise ValueError("n musí být kladné celé číslo")
    a, b = 0, 1
    for _ in range(1, n):
        a, b = b, a + b
    return a

def main():
    import sys
    if len(sys.argv) != 2:
        print("Použití: python test_fib.py <pořadí>")
        sys.exit(1)
    try:
        n = int(sys.argv[1])
        print(f"Fibonacciho číslo na pozici {n}: {fibonacci(n)}")
    except ValueError as e:
        print(f"Chyba: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()