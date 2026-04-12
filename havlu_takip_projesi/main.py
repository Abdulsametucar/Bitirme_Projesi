import cv2
from datetime import datetime
from flask import Flask, render_template, Response, jsonify
from cv_engine.detector import detect_towel
from cv_engine.tracker import TowelStateMachine
from cv_engine.video_stream import VideoStream
from database.db_config import init_db
from database.crud import get_summary, create_towel_process, get_or_create_worker

app = Flask(__name__)
init_db()

VIDEO_SOURCE = 'data/sample_video.mp4'

stream = VideoStream(VIDEO_SOURCE)
tracker = TowelStateMachine()


def frame_generator():
    worker = get_or_create_worker('default')
    frame_count = 0

    while True:
        frame = stream.read()
        if frame is None:
            break

        result = detect_towel(frame)
        if result['bbox'] is not None:
            x, y, w, h = result['bbox']
            tracker_event = tracker.update(w, h)
            step_text = tracker_event.get('current_step', 'Bekleniyor')
            cv2.putText(frame, f'Adim: {step_text}', (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f'Kalinlik: {result["w"]}x{result["h"]}', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if tracker_event.get('completed'):
                process_data = tracker_event['process']
                create_towel_process(
                    worker,
                    process_data['start_time'],
                    process_data['end_time'],
                    process_data['correct_fold'],
                    process_data['total_steps'],
                    process_data['duration_seconds'],
                    process_data['steps'],
                )
                tracker.reset()

        encoded, buffer = cv2.imencode('.jpg', frame)
        frame_data = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        frame_count += 1

        if frame_count > 2000:
            stream.reset()
            frame_count = 0


@app.route('/')
def index():
    summary = get_summary()
    return render_template('index.html', summary=summary)


@app.route('/live')
def live():
    return render_template('live_feed.html')


@app.route('/video_feed')
def video_feed():
    return Response(frame_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/summary')
def api_summary():
    return jsonify(get_summary())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
