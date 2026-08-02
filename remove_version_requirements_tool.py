def main():
    with open("./requirements.txt", "r", encoding="utf-16") as f:
        lines = f.readlines()

    modified_lines = []
    for line in lines:
        stripped_line = line.split("==", 1)[0]

        if not stripped_line.endswith("\n"):
            stripped_line += "\n"

        modified_lines.append(stripped_line)

    with open("./new_requirements.txt", "w", encoding="utf-16") as f:
        f.writelines(modified_lines)

if __name__ == "__main__":
    main()