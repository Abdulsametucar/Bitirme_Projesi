"""
tracker.py - Yon-Duyarli Havlu Katlama Durum Makinesi

Detector'dan gelen (x, y, w, h) bounding box verisini kullanarak
havlunun hangi katlama asamasinda oldugunu, katlama YONUNU,
sureleri ve dogru/yanlis sira bilgisini takip eder.

Stabilizasyon (Debounce) Mantigi:
    Katlama aninda iscinin elleri kadraja girdiginde bounding box anlik
    olarak dalgalanir. Sistem, boyutlarin belirli bir sure (stable_frames)
    boyunca %2'lik tolerans bandinda sabit kalmasini bekler. Ancak
    stabilize olmus boyutlar uzerinden karar verir.

Katlama Senaryosu (5 Adim):
    State 0 -> Baslangic (Havlu Acik)     : Ilk bbox kaydedilir
    State 1 -> 1. Katlama (Sagdan)        : Sag kenar (x+w) iceri gelir, sol kenar (x) sabit
    State 2 -> 2. Katlama (Ustten)        : Ust kenar (y) asagi iner, alt kenar (y+h) sabit
    State 3 -> 3. Katlama (Alttan Uste)   : Alt kenar (y+h) yukari cikar, ust kenar (y) sabit
    State 4 -> 4. Katlama (Soldan)        : Sol kenar (x) saga kayar, sag kenar sabit
    State 5 -> 5. Katlama - Final (Soldan): Sol kenar (x) saga kayar, sag kenar sabit
    State 6 -> Tamamlandi
"""

import time
from datetime import datetime


class TowelTracker:
    """
    Yon-duyarli havlu katlama durum makinesi.

    Her frame'de detector'dan gelen (x, y, w, h) degerlerini alir,
    oransal tolerans bantlari ve kenar hareketi ile durumu belirler.
    """

    STATE_NAMES = {
        0: 'Baslangic - Havlu Acik',
        1: '1. Katlama (Sagdan)',
        2: '2. Katlama (Ustten)',
        3: '3. Katlama (Alttan Uste)',
        4: '4. Katlama (Soldan)',
        5: '5. Katlama - Final (Soldan)',
        6: 'Tamamlandi',
    }

    # Gecis tanimlari: State N'den State N+1'e gecis kosullari
    # Oranlar baslangic boyutuna goredir.
    # expected_direction: katlama yonu dogrulama bilgisi
    #   'right_in'  -> sag kenar iceri, sol sabit
    #   'top_in'    -> ust kenar asagi, alt sabit
    #   'bottom_up' -> alt kenar yukari, ust sabit
    #   'left_in'   -> sol kenar saga, sag sabit
    DEFAULT_TRANSITIONS = [
        {   # State 0->1: Sagdan katlama (W ~%15 azalir)
            'change_axis': 'w',
            'expected_direction': 'right_in',
            'w_ratio_range': (0.70, 0.92),
            'h_ratio_range': (0.85, 1.15),
        },
        {   # State 1->2: Ustten katlama (H ~%33 azalir)
            'change_axis': 'h',
            'expected_direction': 'top_in',
            'w_ratio_range': (0.65, 0.95),
            'h_ratio_range': (0.55, 0.82),
        },
        {   # State 2->3: Alttan uste katlama (H ~%50 azalir)
            'change_axis': 'h',
            'expected_direction': 'bottom_up',
            'w_ratio_range': (0.65, 0.95),
            'h_ratio_range': (0.25, 0.55),
        },
        {   # State 3->4: Soldan katlama (W ~%33 azalir)
            'change_axis': 'w',
            'expected_direction': 'left_in',
            'w_ratio_range': (0.38, 0.72),
            'h_ratio_range': (0.20, 0.60),
        },
        {   # State 4->5: Soldan tekrar (Final) (W ~%50 azalir)
            'change_axis': 'w',
            'expected_direction': 'left_in',
            'w_ratio_range': (0.12, 0.45),
            'h_ratio_range': (0.20, 0.75),
        },
    ]

    # Kenar hareketi esik degerleri (piksel cinsinden oran)
    EDGE_MOVE_THRESHOLD = 0.03   # Hareket eden kenar min degisim
    EDGE_STABLE_THRESHOLD = 0.05 # Sabit olmasi gereken kenar max degisim

    def __init__(self, transitions=None, stability_tolerance=0.15,
                 confirmation_frames=3, towel_lost_frames=10,
                 stable_frames=15, stable_tolerance=0.02):
        """
        Args:
            transitions:         Gecis tanimlari listesi.
            stability_tolerance: Eksen hata kontrolu toleransi.
            confirmation_frames: State gecisi icin gereken ardisik frame.
            towel_lost_frames:   Havlu kayip sayilmasi icin bos frame sayisi.
            stable_frames:       Debounce: boyutlarin sabit kalmasi gereken
                                 ardisik frame sayisi (varsayilan 15).
            stable_tolerance:    Debounce: sabit kabul edilecek max degisim
                                 orani (varsayilan 0.02 = %2).
        """
        self.transitions = transitions or self.DEFAULT_TRANSITIONS
        self.stability_tolerance = stability_tolerance
        self.confirmation_frames = confirmation_frames
        self.towel_lost_frames = towel_lost_frames
        self.stable_frames = stable_frames
        self.stable_tolerance = stable_tolerance
        self.reset()

    # =================================================================
    # ANA METOTLAR
    # =================================================================

    def reset(self):
        """Tum durum bilgilerini sifirlar."""
        self.current_state = 0
        self.completed = False
        self.is_error = False

        # Baslangic bbox ve boyutlari
        self.initial_x = None
        self.initial_y = None
        self.initial_w = None
        self.initial_h = None

        # Onceki frame bbox (yon kontrolu icin)
        self._prev_x = None
        self._prev_y = None
        self._prev_w = None
        self._prev_h = None

        # State giris bbox (yon kontrolu icin referans)
        self._entry_x = None
        self._entry_y = None
        self._entry_w = None
        self._entry_h = None

        # Zaman takibi (perf_counter bazli)
        self._perf_process_start = None
        self._perf_state_start = None
        self._perf_process_end = None
        self.process_start_time = None
        self.process_end_time = None
        self.state_durations = {}

        # Sayaclar
        self._confirm_count = 0
        self._skip_confirm_count = 0
        self._axis_error_count = 0
        self._direction_error_count = 0
        self._lost_count = 0
        self._transition_cooldown = 0

        # Son bilinen oranlar
        self._last_w_ratio = 1.0
        self._last_h_ratio = 1.0
        self._state_entry_w_ratio = 1.0
        self._state_entry_h_ratio = 1.0

        # ── STABILIZASYON (DEBOUNCE) ──
        # Boyutlar stabil olana kadar karar verilmez.
        # _stable_count: ard arda kac frame boyunca boyutlar sabit kaldi
        # _stable_ref_*: stabilizasyon referans degerleri
        # _is_stable: mevcut olcumlerin stabil oldugu flag
        self._stable_count = 0
        self._stable_ref_x = 0
        self._stable_ref_y = 0
        self._stable_ref_w = 0
        self._stable_ref_h = 0
        self._is_stable = False
        # Stabil son degerler (karar verme icin kullanilir)
        self._stable_x = 0
        self._stable_y = 0
        self._stable_w = 0
        self._stable_h = 0

        self.errors = []
        self.steps = []

    def update(self, x, y, w, h):
        """
        Her frame'de cagrilir.

        Gelen bbox degerleri oncelikle stabilizasyon filtresinden gecirilir.
        Boyutlar stabil olana kadar (stable_frames boyunca %2 tolerans icinde)
        state machine karari verilmez. Bu sayede iscinin elleri kadraja
        girdiginde anlik dalgalanmalar ignore edilir.

        Args:
            x, y: Bounding box sol ust kose (px). 0 = havlu yok.
            w, h: Bounding box genislik/yukseklik (px). 0 = havlu yok.

        Returns:
            dict: Anlik durum raporu.
        """
        now_perf = time.perf_counter()
        now_dt = datetime.now()

        if not w or not h:
            self._stable_count = 0
            self._is_stable = False
            return self._handle_towel_lost(now_perf, now_dt)

        self._lost_count = 0

        # ── STABILIZASYON FILTRESI ──
        # Boyutlarin referans degerlere gore %2 icinde olup olmadigini kontrol et
        if self._stable_ref_w > 0 and self._stable_ref_h > 0:
            w_change = abs(w - self._stable_ref_w) / self._stable_ref_w
            h_change = abs(h - self._stable_ref_h) / self._stable_ref_h

            if w_change <= self.stable_tolerance and h_change <= self.stable_tolerance:
                # Boyutlar referansa yakin -> stabil sayaci artir
                self._stable_count += 1
            else:
                # Boyutlar degisti -> yeni referans baslat
                self._stable_ref_x, self._stable_ref_y = x, y
                self._stable_ref_w, self._stable_ref_h = w, h
                self._stable_count = 1
                self._is_stable = False
        else:
            # Ilk olcum -> referans olarak kaydet
            self._stable_ref_x, self._stable_ref_y = x, y
            self._stable_ref_w, self._stable_ref_h = w, h
            self._stable_count = 1
            self._is_stable = False

        # Stabil mi? (yeterli frame boyunca sabit kaldi)
        if self._stable_count >= self.stable_frames:
            self._is_stable = True
            self._stable_x, self._stable_y = x, y
            self._stable_w, self._stable_h = w, h

        # Ilk kare
        if self.initial_w is None:
            if self._is_stable:
                self._initialize(x, y, w, h, now_perf, now_dt)
            return self.get_status()

        if self.completed or self.current_state >= 6:
            return self.get_status()

        # ── STABIL DEGERLERI KULLANARAK KARAR VER ──
        # Boyutlar dalgalaniyorsa (is_stable=False) state machine bekler.
        # Sadece stabilize olmus degerler uzerinden gecis/hata kontrolu yapilir.
        if not self._is_stable:
            # Dalgalanma devam ediyor -> onceki oranlari koru, bekle
            return self.get_status()

        # Stabil boyutlar uzerinden oranlari hesapla
        sx, sy, sw, sh = self._stable_x, self._stable_y, self._stable_w, self._stable_h
        w_ratio = sw / self.initial_w
        h_ratio = sh / self.initial_h

        # Gecis kontrolu
        if self.current_state < len(self.transitions):
            transition = self.transitions[self.current_state]

            if self._ratios_match(w_ratio, h_ratio, transition):
                dir_ok = self._check_direction(sx, sy, sw, sh, transition)
                if dir_ok:
                    self._confirm_count += 1
                    self._skip_confirm_count = 0
                    self._direction_error_count = 0
                    if self._confirm_count >= self.confirmation_frames:
                        self._do_transition(sx, sy, sw, sh,
                                            w_ratio, h_ratio,
                                            now_perf, now_dt)
                else:
                    self._direction_error_count += 1
                    if self._direction_error_count >= self.confirmation_frames:
                        self._fire_direction_error(
                            sx, sy, sw, sh, transition, now_perf, now_dt)
            else:
                self._confirm_count = 0
                self._direction_error_count = 0
                if self._transition_cooldown > 0:
                    self._transition_cooldown -= 1
                else:
                    self._check_wrong_order(w_ratio, h_ratio, now_perf, now_dt)

        # Onceki bbox ve oranlar guncelle
        self._prev_x, self._prev_y = sx, sy
        self._prev_w, self._prev_h = sw, sh
        self._last_w_ratio = w_ratio
        self._last_h_ratio = h_ratio

        return self.get_status()

    def get_status(self):
        """Anlik durum raporunu dict olarak dondurur."""
        now_perf = time.perf_counter()
        state_name = self.STATE_NAMES.get(self.current_state, 'Bilinmiyor')

        total_elapsed = 0.0
        state_elapsed = 0.0
        if self._perf_process_start is not None:
            end = self._perf_process_end or now_perf
            total_elapsed = end - self._perf_process_start
        if self._perf_state_start is not None:
            if self._perf_process_end is not None:
                state_elapsed = self.state_durations.get(
                    self.current_state,
                    self._perf_process_end - self._perf_state_start)
            else:
                state_elapsed = now_perf - self._perf_state_start

        process_data = self._build_process() if self.completed else None

        return {
            'current_state': self.current_state,
            'state_name': state_name,
            'current_step': state_name,
            'w_ratio': round(self._last_w_ratio, 3),
            'h_ratio': round(self._last_h_ratio, 3),
            'elapsed_total': round(total_elapsed, 2),
            'elapsed_state': round(state_elapsed, 2),
            'state_durations': dict(self.state_durations),
            'completed': self.completed,
            'is_error': self.is_error,
            'is_stable': self._is_stable,
            'errors': list(self.errors),
            'steps': list(self.steps),
            'process': process_data,
        }

    def get_status_text(self):
        """Okunakli konsol raporu."""
        s = self.get_status()
        lines = [
            "=" * 50,
            f"  State    : [{s['current_state']}] {s['state_name']}",
            f"  W Orani  : {s['w_ratio']:.3f}  |  H Orani : {s['h_ratio']:.3f}",
            f"  Toplam   : {s['elapsed_total']:.1f} sn  |  Bu adim : {s['elapsed_state']:.1f} sn",
            f"  Tamamlandi: {'Evet' if s['completed'] else 'Hayir'}",
        ]
        if s['errors']:
            lines.append(f"  HATALAR : {len(s['errors'])} adet")
            for err in s['errors']:
                lines.append(f"     - {err}")
        lines.append("=" * 50)
        return '\n'.join(lines)

    def get_report(self):
        """Islem sonu detayli rapor."""
        s = self.get_status()
        lines = ["", "=" * 62, "          HAVLU KATLAMA - ISLEM RAPORU", "=" * 62]

        if self.initial_w and self.initial_h:
            lines.append(f"  Baslangic Boyutu : {self.initial_w} x {self.initial_h} px")
        lines.append(f"  Toplam Sure      : {s['elapsed_total']:.2f} saniye")
        lines.append("")

        lines.append("  -- Adim Sureleri ------------------------------------")
        if self.steps:
            for i, step in enumerate(self.steps):
                dur = step.get('duration_seconds', 0.0)
                lines.append(
                    f"  {i+1}. {step['name']:<30s}  "
                    f"W:{step['w_ratio']:.3f}  H:{step['h_ratio']:.3f}  "
                    f"| {dur:.2f} sn")
        else:
            lines.append("  (Henuz tamamlanan adim yok)")

        lines.append("")
        lines.append("  -- State Bazli Sureler ------------------------------")
        for sid in sorted(self.state_durations.keys()):
            lines.append(f"  State {sid} ({self.STATE_NAMES.get(sid,'?')}): "
                         f"{self.state_durations[sid]:.2f} sn")

        if self.errors:
            lines.append("")
            lines.append("  -- HATALAR ------------------------------------------")
            for err in self.errors:
                lines.append(f"  X {err}")

        lines.append("")
        lines.append("=" * 62)
        if s['is_error']:
            lines.append("  SONUC:  X HATALI KATLAMA (BASARISIZ)")
        elif s['completed'] and not s['is_error']:
            lines.append("  SONUC:  V BASARILI KATLAMA")
        else:
            lines.append("  SONUC:  - ISLEM DEVAM EDIYOR / TAMAMLANMADI")
        lines.append("=" * 62)
        lines.append("")
        return '\n'.join(lines)

    # =================================================================
    # PRIVATE METOTLAR
    # =================================================================

    def _initialize(self, x, y, w, h, perf_time, dt_time):
        """Ilk kare: baslangic bilgilerini kaydet."""
        self.initial_x, self.initial_y = x, y
        self.initial_w, self.initial_h = w, h
        self._prev_x, self._prev_y = x, y
        self._prev_w, self._prev_h = w, h
        self._entry_x, self._entry_y = x, y
        self._entry_w, self._entry_h = w, h
        self._perf_process_start = perf_time
        self._perf_state_start = perf_time
        self.process_start_time = dt_time
        self.current_state = 0
        self._last_w_ratio = 1.0
        self._last_h_ratio = 1.0
        self._state_entry_w_ratio = 1.0
        self._state_entry_h_ratio = 1.0

    def _ratios_match(self, w_ratio, h_ratio, transition):
        """Tolerans bandi kontrolu (== KULLANILMAZ)."""
        w_min, w_max = transition['w_ratio_range']
        h_min, h_max = transition['h_ratio_range']
        return (w_min <= w_ratio <= w_max) and (h_min <= h_ratio <= h_max)

    def _check_direction(self, x, y, w, h, transition):
        """
        Katlama yonunu dogrular.

        Bounding box kenarlarinin hareketine bakarak katlamanin beklenen
        yonden yapilip yapilmadigini kontrol eder.

        Returns:
            True: Yon dogru veya kontrol edilemiyor
            False: Yanlis yon tespit edildi
        """
        if self._entry_w is None or self._entry_h is None:
            return True

        direction = transition.get('expected_direction')
        if not direction:
            return True

        ref_w = self._entry_w
        ref_h = self._entry_h

        # Kenar pozisyonlari (giris anina gore)
        entry_left = self._entry_x
        entry_right = self._entry_x + self._entry_w
        entry_top = self._entry_y
        entry_bottom = self._entry_y + self._entry_h

        cur_left = x
        cur_right = x + w
        cur_top = y
        cur_bottom = y + h

        move_thr = self.EDGE_MOVE_THRESHOLD * max(ref_w, ref_h)
        stable_thr = self.EDGE_STABLE_THRESHOLD * max(ref_w, ref_h)

        if direction == 'right_in':
            # Sag kenar iceri gelmeli, sol kenar sabit
            right_moved = entry_right - cur_right  # Pozitif = iceri
            left_moved = abs(cur_left - entry_left)
            if left_moved > stable_thr and right_moved < move_thr:
                return False  # Soldan katlanmis

        elif direction == 'top_in':
            # Ust kenar asagi inmeli, alt kenar sabit
            top_moved = cur_top - entry_top  # Pozitif = asagi
            bottom_moved = abs(cur_bottom - entry_bottom)
            if bottom_moved > stable_thr and top_moved < move_thr:
                return False  # Alttan katlanmis

        elif direction == 'bottom_up':
            # Alt kenar yukari cikmali, ust kenar sabit
            bottom_moved = entry_bottom - cur_bottom  # Pozitif = yukari
            top_moved = abs(cur_top - entry_top)
            if top_moved > stable_thr and bottom_moved < move_thr:
                return False  # Ustten katlanmis

        elif direction == 'left_in':
            # Sol kenar saga kaymali, sag kenar sabit
            left_moved = cur_left - entry_left  # Pozitif = saga
            right_moved = abs(cur_right - entry_right)
            if right_moved > stable_thr and left_moved < move_thr:
                return False  # Sagdan katlanmis

        return True

    def _fire_direction_error(self, x, y, w, h, transition, perf_time, dt_time):
        """Yanlis yon hatasi firlat ve islemi durdur."""
        direction = transition.get('expected_direction', '?')
        direction_names = {
            'right_in': 'Sagdan',
            'top_in': 'Ustten',
            'bottom_up': 'Alttan Uste',
            'left_in': 'Soldan',
        }
        expected = direction_names.get(direction, direction)

        # Ters yonu bul
        opposites = {
            'right_in': 'Soldan',
            'top_in': 'Alttan',
            'bottom_up': 'Ustten',
            'left_in': 'Sagdan',
        }
        actual = opposites.get(direction, 'Bilinmeyen yon')

        msg = (f"HATALI KATLAMA YONU: State {self.current_state}'de "
               f"beklenen: {expected} katlama, "
               f"ancak {actual} katlama tespit edildi.")
        self.errors.append(msg)
        self.is_error = True
        self.completed = True
        self._perf_process_end = perf_time
        self.process_end_time = dt_time
        self._save_current_state_duration(perf_time)

    def _do_transition(self, x, y, w, h, w_ratio, h_ratio, perf_time, dt_time):
        """Bir sonraki state'e gec."""
        self._save_current_state_duration(perf_time)

        old_state = self.current_state
        self.current_state += 1
        self._confirm_count = 0
        self._skip_confirm_count = 0
        self._axis_error_count = 0
        self._direction_error_count = 0
        self._transition_cooldown = self.confirmation_frames * 3
        self._perf_state_start = perf_time

        # Yeni state icin giris referanslarini kaydet
        self._entry_x, self._entry_y = x, y
        self._entry_w, self._entry_h = w, h
        self._state_entry_w_ratio = w_ratio
        self._state_entry_h_ratio = h_ratio

        self.steps.append({
            'name': self.STATE_NAMES.get(self.current_state, '?'),
            'from_state': old_state,
            'to_state': self.current_state,
            'timestamp': dt_time,
            'duration_seconds': self.state_durations.get(old_state, 0.0),
            'w_ratio': round(w_ratio, 3),
            'h_ratio': round(h_ratio, 3),
        })

        # State 5'e (Final Katlama) ulasildiginda islem BASARILI olarak biter.
        # Havlunun masadan kalkmasini beklemeye gerek yok.
        if self.current_state >= 5:
            self.completed = True
            self._perf_process_end = perf_time
            self.process_end_time = dt_time
            self._save_current_state_duration(perf_time)

    def _handle_towel_lost(self, perf_time, dt_time):
        """Havlu goruntuден kayboldu."""
        self._lost_count += 1
        self._confirm_count = 0

        if self._lost_count >= self.towel_lost_frames:
            if self.current_state >= 5:
                self.current_state = 6
                self.completed = True
                self._perf_process_end = perf_time
                self.process_end_time = dt_time
                if self._perf_state_start is not None:
                    dur = perf_time - self._perf_state_start
                    self.state_durations[5] = round(dur, 3)
            elif self.initial_w is not None:
                self.errors.append(
                    f"Havlu State {self.current_state}'de masadan kalkti "
                    f"(tamamlanmadi)")
                self.is_error = True
                self.completed = True
                self._perf_process_end = perf_time
                self.process_end_time = dt_time
                self._save_current_state_duration(perf_time)

        return self.get_status()

    def _check_wrong_order(self, w_ratio, h_ratio, perf_time, dt_time):
        """Ileri atlama ve eksen hata kontrolu."""
        if self.current_state >= len(self.transitions):
            return

        # 1. Ileri atlama kontrolu
        skip_detected = False
        for skip_idx in range(self.current_state + 1, len(self.transitions)):
            future = self.transitions[skip_idx]
            if self._ratios_match(w_ratio, h_ratio, future):
                self._skip_confirm_count += 1
                if self._skip_confirm_count >= self.confirmation_frames:
                    skipped = skip_idx - self.current_state
                    exp_next = self.current_state + 1
                    act_target = skip_idx + 1
                    msg = (f"HATALI ISLEM - ADIM ATLANDI: "
                           f"State {self.current_state}'den sonra beklenen: "
                           f"State {exp_next} ({self.STATE_NAMES.get(exp_next,'?')}), "
                           f"ancak State {act_target} ({self.STATE_NAMES.get(act_target,'?')}) "
                           f"tespit edildi ({skipped} adim atlandi).")
                    self.errors.append(msg)
                    self.is_error = True
                    self.completed = True
                    self._perf_process_end = perf_time
                    self.process_end_time = dt_time
                    self._save_current_state_duration(perf_time)
                skip_detected = True
                break

        if skip_detected:
            return
        self._skip_confirm_count = 0

        # 2. Eksen hata kontrolu
        transition = self.transitions[self.current_state]
        change_axis = transition['change_axis']
        tol = self.stability_tolerance

        w_drift = abs(w_ratio - self._state_entry_w_ratio)
        h_drift = abs(h_ratio - self._state_entry_h_ratio)

        axis_violation = False
        if change_axis == 'w' and h_drift > tol and w_drift < 0.05:
            axis_violation = True
            drift_axis, drift_val = 'H', h_drift
        elif change_axis == 'h' and w_drift > tol and h_drift < 0.05:
            axis_violation = True
            drift_axis, drift_val = 'W', w_drift

        if axis_violation:
            self._axis_error_count += 1
            if self._axis_error_count >= self.confirmation_frames:
                expected = 'W' if change_axis == 'w' else 'H'
                msg = (f"Yanlis Eksen: State {self.current_state}'de {expected} "
                       f"degismesi beklenirken {drift_axis} degisti "
                       f"({drift_axis.lower()}_drift={drift_val:.3f})")
                if msg not in self.errors:
                    self.errors.append(msg)
                    self.is_error = True
                    self.completed = True
                    self._perf_process_end = perf_time
                    self.process_end_time = dt_time
                    self._save_current_state_duration(perf_time)
        else:
            self._axis_error_count = 0

    def _save_current_state_duration(self, perf_time):
        """Mevcut state suresini kaydet."""
        if self._perf_state_start is not None:
            dur = perf_time - self._perf_state_start
            self.state_durations[self.current_state] = round(dur, 3)

    def _build_process(self):
        """Surec ozeti dict'i olustur."""
        end_dt = self.process_end_time or datetime.now()
        start_dt = self.process_start_time or end_dt

        if self._perf_process_start and self._perf_process_end:
            duration = self._perf_process_end - self._perf_process_start
        else:
            duration = (end_dt - start_dt).total_seconds()

        total_steps = len(self.steps)
        correct_fold = (total_steps >= 5) and (not self.is_error)

        return {
            'start_time': start_dt,
            'end_time': end_dt,
            'duration_seconds': round(duration, 2),
            'total_steps': total_steps,
            'correct_fold': correct_fold,
            'steps': self.steps,
            'state_durations': dict(self.state_durations),
            'errors': list(self.errors),
        }


# Geriye uyumluluk
TowelStateMachine = TowelTracker
