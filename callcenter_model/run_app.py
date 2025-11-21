import argparse
from callcenter_model.logic.runtime import RuntimeLoop


# Табличный вывод пошагового состояния.
# И0, И1 идут шаги времени, а П0, П1 операторы.
def print_step_table(snaps):
    if not snaps:
        print("Нет данных для вывода.")
        return

    last_snap = snaps[-1]

    print("\n┌─────┬─────────┬──────────────┬──────────────┬──────────────┐")
    print("│ Имя │  Время  │   Признак    │ Число заявок │ Число отказов│")
    print("├─────┼─────────┼──────────────┼──────────────┼──────────────┤")

    # Здесь выводятся шаги И0, И1, И2
    for i, snap in enumerate(snaps):
        t = snap["t"]

        # Заявки считаем так: сколько в буфере + сколько у операторов занято
        buf_count = snap["pool"]["count"]
        busy_ops = sum(1 for op in snap["ops"] if op["mode"] == "busy")
        total_calls = buf_count + busy_ops

        status = "Событие" if snap["events"] else "Ожидает"

        # Процент отказов (или 0)
        rej = snap["rej"]
        rej_out = f"{rej:.0f}" if rej.is_integer() else f"{rej:.2f}"

        print(
            f"│ И{i:<2}│ {t:7.3f} │ {status:<12} │ "
            f"{total_calls:<12} │ {rej_out:<12} │"
        )

    for op in last_snap["ops"]:
        t = last_snap["t"]
        name = f"П{op['id']}"
        mode = "Занят" if op["mode"] == "busy" else "Свободен"

        # Если оператор занят — у него 1 текущая заявка, иначе "-"
        calls_now = "1" if op["mode"] == "busy" else "-"

        print(
            f"│ {name:<3}│ {t:7.3f} │ {mode:<12} │ "
            f"{calls_now:<12} │ {'-':<12} │"
        )

    print("└─────┴─────────┴──────────────┴──────────────┴──────────────┘\n")


# Пошаговый режим моделирования
def run_step(engine: RuntimeLoop, steps: int):
    snaps = engine.run_steps(steps)
    print_step_table(snaps)


# Автоматический режим
def run_auto(engine: RuntimeLoop, duration: float, out_dir: str):
    rep = engine.run_auto(duration, out_dir)

    print("\nИтоги моделирования:")
    print(f"Длительность:           {rep['total']:.2f}")
    print(f"Сгенерировано:          {rep['generated']}")
    print(f"Обслужено:              {rep['done']}")
    print(f"Отказов:                {rep['rejected']}")
    print(f"Процент отказов:        {rep['rej_percent']:.2f}%")
    print(f"Средн. ожидание:        {rep['avg_wait']:.2f}")
    print(f"Средн. обслуживание:    {rep['avg_serv']:.2f}")
    print(f"Графики сохранены в:    {rep['graph']}\n")


# Тут просто аргументы командной строки
def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["step", "auto"], default="step")
    p.add_argument("--steps", type=int, default=30)
    p.add_argument("--time", type=float, default=50.0)
    p.add_argument("--buf", type=int, default=8)
    p.add_argument("--w", type=int, default=3)
    p.add_argument("--l1", type=float, default=0.5)
    p.add_argument("--l2", type=float, default=0.6)
    p.add_argument("--out", type=str, default="new_artifacts")
    return p


def main():
    args = build_parser().parse_args()

    # Два источника: ИБ и ИЗ1
    rates = [args.l1, args.l2]

    engine = RuntimeLoop(rates, args.buf, args.w)

    if args.mode == "step":
        run_step(engine, args.steps)
    else:
        run_auto(engine, args.time, args.out)


if __name__ == "__main__":
    main()
