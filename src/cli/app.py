from src.services.cinema_service import CinemaService
from src.cli.parser import run_line

def main():
    svc = CinemaService()
    print("Cinema Ticket System (in-memory). Type EXIT to quit.")
    while True:
        try:
            line = input(">> ").strip()
            if not line:
                continue
            if line.upper() in ("EXIT", "QUIT"):
                print("Bye.")
                break
            print(run_line(svc, line))
        except EOFError:
            break

if __name__ == "__main__":
    main()
