from database.db_config import get_session
from database.models import Worker, TowelProcess, Step


def get_or_create_worker(name='default'):
    session = get_session()
    worker = session.query(Worker).filter_by(name=name).first()
    if not worker:
        worker = Worker(name=name)
        session.add(worker)
        session.commit()
    session.close()
    return worker


def create_towel_process(worker, start_time, end_time, correct_fold, total_steps, duration_seconds, steps):
    session = get_session()
    process = TowelProcess(
        worker_id=worker.id,
        start_time=start_time,
        end_time=end_time,
        correct_fold=correct_fold,
        total_steps=total_steps,
        duration_seconds=duration_seconds,
    )
    session.add(process)
    session.flush()

    for step in steps:
        session.add(Step(
            process_id=process.id,
            name=step['name'],
            timestamp=step['timestamp'],
            duration_seconds=step['duration_seconds'],
        ))

    session.commit()
    session.close()
    return process


def get_summary():
    session = get_session()
    total = session.query(TowelProcess).count()
    top_worker = session.query(Worker.name, TowelProcess.correct_fold).join(TowelProcess).group_by(Worker.id).all()
    worker_stats = {}
    for name, correct_fold in top_worker:
        worker_stats.setdefault(name, {'count': 0, 'correct': 0})
        worker_stats[name]['count'] += 1
        if correct_fold:
            worker_stats[name]['correct'] += 1

    best_worker = None
    best_rate = 0.0
    for name, stats in worker_stats.items():
        rate = stats['correct'] / stats['count'] if stats['count'] else 0.0
        if rate > best_rate:
            best_rate = rate
            best_worker = name

    summary = {
        'total_towels': total,
        'best_worker': best_worker or 'Yok',
        'best_rate': round(best_rate * 100, 1),
        'worker_stats': worker_stats,
    }
    session.close()
    return summary
