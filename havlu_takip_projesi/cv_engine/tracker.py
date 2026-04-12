"""
tracker.py – Toleranslı Havlu Katlama Durum Makinesi (State Machine)

Detector'dan gelen anlık genişlik (w) ve yükseklik (h) verilerini alarak,
havlunun hangi katlama aşamasında olduğunu, süreleri ve doğru/yanlış sıra
bilgisini takip eder.

Katlama Senaryosu (5 Adım):
    State 0 → Başlangıç (Havlu Açık)         : İlk boyutlar kaydedilir
    State 1 → 1. Katlama (Sağdan)             : W ~%15 azalır, H sabit
    State 2 → 2. Katlama (Üstten)             : H ~%33 azalır, W sabit
    State 3 → 3. Katlama (Üstten – Tekrar)    : H ~%50 azalır (initial'e göre), W sabit
    State 4 → 4. Katlama (Soldan)             : W ~%33 azalır, H sabit
    State 5 → 5. Katlama – Final (Soldan)     : W ~%50 azalır, H sabit
    State 6 → Tamamlandı                      : Havlu masadan kalktı

KESİNLİKLE == KULLANILMAZ. Her kontrol tolerans bantları içinde yapılır.
"""

import time
from datetime import datetime


class TowelTracker:
    """
    Toleranslı havlu katlama durum makinesi.

    Her frame'de detector'dan gelen (w, h) değerlerini alır,
    oransal tolerans bantlarıyla durumu belirler ve süreleri takip eder.

    Kullanım:
        tracker = TowelTracker()
        result = tracker.update(current_w, current_h)
        print(result)  # veya tracker.get_status()
    """

    # ── DURUM İSİMLERİ ──────────────────────────────────────────
    STATE_NAMES = {
        0: 'Başlangıç – Havlu Açık',
        1: '1. Katlama (Sağdan)',
        2: '2. Katlama (Üstten)',
        3: '3. Katlama (Üstten – Tekrar)',
        4: '4. Katlama (Soldan)',
        5: '5. Katlama – Final (Soldan)',
        6: 'Tamamlandı',
    }

    # ── GEÇİŞ TANIMLARI ────────────────────────────────────────
    # Her eleman: State N'den State N+1'e geçiş koşulları.
    # Oranlar HER ZAMAN başlangıç boyutuna (initial_w, initial_h) göredir.
    #
    #   change_axis   : Bu geçişte değişmesi beklenen eksen ('w' veya 'h')
    #   w_ratio_range : (min, max) – w/initial_w beklenen tolerans aralığı
    #   h_ratio_range : (min, max) – h/initial_h beklenen tolerans aralığı
    #
    # Gerçek verilerle kalibre edilmiştir (Adim_1 → Adim_7).
    #
    DEFAULT_TRANSITIONS = [
        # ── State 0 → 1: Sağdan katlama ─────────────────────
        # W ~%15-20 azalır → w_ratio ≈ 0.80 | H sabit
        {
            'change_axis': 'w',
            'w_ratio_range': (0.70, 0.92),
            'h_ratio_range': (0.85, 1.15),
        },
        # ── State 1 → 2: Üstten katlama ─────────────────────
        # H ~%30 azalır → h_ratio ≈ 0.70 | W sabit (~0.80 seviyesinde)
        {
            'change_axis': 'h',
            'w_ratio_range': (0.65, 0.95),
            'h_ratio_range': (0.55, 0.82),
        },
        # ── State 2 → 3: Üstten tekrar katlama ──────────────
        # H ~%62 azalır → h_ratio ≈ 0.38 | W sabit
        {
            'change_axis': 'h',
            'w_ratio_range': (0.65, 0.95),
            'h_ratio_range': (0.25, 0.55),
        },
        # ── State 3 → 4: Soldan katlama ──────────────────────
        # W ciddi azalır → w_ratio ≈ 0.55 | H sabit (~0.38 seviyesinde)
        {
            'change_axis': 'w',
            'w_ratio_range': (0.38, 0.72),
            'h_ratio_range': (0.20, 0.60),
        },
        # ── State 4 → 5: Soldan tekrar katlama (Final) ──────
        # W daha da azalır → w_ratio ≈ 0.28 | H sabit
        {
            'change_axis': 'w',
            'w_ratio_range': (0.12, 0.45),
            'h_ratio_range': (0.20, 0.75),
        },
    ]

    def __init__(self,
                 transitions=None,
                 stability_tolerance=0.15,
                 confirmation_frames=3,
                 towel_lost_frames=10):
        """
        Args:
            transitions:         Geçiş tanımları listesi (None = varsayılan).
            stability_tolerance: Sabit eksen için izin verilen değişim oranı
                                 (±%). Varsayılan 0.15 = %15.
            confirmation_frames: Bir state geçişi için gereken ardışık
                                 eşleşen kare sayısı. Titreşim filtresi.
            towel_lost_frames:   Havlu "kayıp" sayılması için gereken
                                 ardışık boş kare sayısı.
        """
        self.transitions = transitions or self.DEFAULT_TRANSITIONS
        self.stability_tolerance = stability_tolerance
        self.confirmation_frames = confirmation_frames
        self.towel_lost_frames = towel_lost_frames
        self.reset()

    # ═══════════════════════════════════════════════════════════════
    # ANA METOTLAR
    # ═══════════════════════════════════════════════════════════════

    def reset(self):
        """Tüm durum bilgilerini sıfırlar. Yeni katlama süreci başlatır."""
        self.current_state = 0
        self.initial_w = None
        self.initial_h = None
        self.completed = False
        self.is_error = False

        # Zaman takibi
        self.process_start_time = None
        self.state_start_time = None
        self.state_durations = {}          # {state_id: süre (saniye)}
        self.process_end_time = None

        # Sayaçlar
        self._confirm_count = 0
        self._lost_count = 0

        # Son bilinen oranlar
        self._last_w_ratio = 1.0
        self._last_h_ratio = 1.0

        # Hata kayıtları
        self.errors = []

        # Geçiş geçmişi: her geçiş bir dict olarak kaydedilir
        self.steps = []

    def update(self, current_w, current_h):
        """
        Her frame'de çağrılır. Detector'dan gelen boyutları alır ve
        durum makinesini günceller.

        Args:
            current_w: Anlık havlu genişliği (px). None/0 = havlu yok.
            current_h: Anlık havlu yüksekliği (px). None/0 = havlu yok.

        Returns:
            dict: Anlık durum raporu (get_status() ile aynı format).
        """
        now = datetime.utcnow()

        # ── Havlu masada mı? ───────────────────────────────────
        if not current_w or not current_h:
            return self._handle_towel_lost(now)

        self._lost_count = 0  # Havlu görüldü → kayıp sayacını sıfırla

        # ── İlk kare: başlangıç boyutlarını kaydet ────────────
        if self.initial_w is None:
            self._initialize(current_w, current_h, now)
            return self.get_status()

        # ── Zaten tamamlandıysa güncelleme yapma ───────────────
        if self.completed or self.current_state >= 6:
            return self.get_status()

        # ── Oranları hesapla (başlangıca göre) ─────────────────
        w_ratio = current_w / self.initial_w
        h_ratio = current_h / self.initial_h

        # ── Geçiş kontrolü ────────────────────────────────────
        if self.current_state < len(self.transitions):
            transition = self.transitions[self.current_state]

            if self._ratios_match(w_ratio, h_ratio, transition):
                self._confirm_count += 1
                if self._confirm_count >= self.confirmation_frames:
                    self._do_transition(w_ratio, h_ratio, now)
            else:
                self._confirm_count = 0
                # Yanlış sıra kontrolü
                self._check_wrong_order(w_ratio, h_ratio, now)

        # Son oranları güncelle
        self._last_w_ratio = w_ratio
        self._last_h_ratio = h_ratio

        return self.get_status()

    def get_status(self):
        """
        Anlık durum raporunu dict olarak döndürür.

        Returns:
            dict: {
                'current_state':  int,
                'state_name':     str,
                'current_step':   str,       # Geriye uyumluluk (main.py)
                'w_ratio':        float,
                'h_ratio':        float,
                'elapsed_total':  float,     # Toplam geçen süre (sn)
                'elapsed_state':  float,     # Bu state'te geçen süre (sn)
                'state_durations': dict,
                'completed':      bool,
                'is_error':       bool,
                'errors':         list,
                'steps':          list,
                'process':        dict/None, # Tamamlandıysa süreç özeti
            }
        """
        now = time.time()
        state_name = self.STATE_NAMES.get(self.current_state, 'Bilinmiyor')

        # Süre hesapları
        total_elapsed = 0.0
        state_elapsed = 0.0
        if self.process_start_time:
            end = self.process_end_time or datetime.utcnow()
            total_elapsed = (end - self.process_start_time).total_seconds()
        if self.state_start_time:
            state_elapsed = (datetime.utcnow() - self.state_start_time).total_seconds()

        # Süreç özeti (tamamlandıysa)
        process_data = None
        if self.completed:
            process_data = self._build_process()

        return {
            'current_state': self.current_state,
            'state_name': state_name,
            'current_step': state_name,             # Geriye uyumluluk
            'w_ratio': round(self._last_w_ratio, 3),
            'h_ratio': round(self._last_h_ratio, 3),
            'elapsed_total': round(total_elapsed, 2),
            'elapsed_state': round(state_elapsed, 2),
            'state_durations': dict(self.state_durations),
            'completed': self.completed,
            'is_error': self.is_error,
            'errors': list(self.errors),
            'steps': list(self.steps),
            'process': process_data,
        }

    def get_status_text(self):
        """Okunaklı string rapor döndürür (konsol çıktısı için)."""
        s = self.get_status()
        lines = [
            f"══════════════════════════════════════════",
            f"  State    : [{s['current_state']}] {s['state_name']}",
            f"  W Oranı  : {s['w_ratio']:.3f}  |  H Oranı : {s['h_ratio']:.3f}",
            f"  Toplam   : {s['elapsed_total']:.1f} sn  |  Bu adım : {s['elapsed_state']:.1f} sn",
            f"  Tamamlandı: {'Evet ✓' if s['completed'] else 'Hayır'}",
        ]
        if s['errors']:
            lines.append(f"  ⚠ Hatalar : {len(s['errors'])} adet")
            for err in s['errors']:
                lines.append(f"     - {err}")
        lines.append(f"══════════════════════════════════════════")
        return '\n'.join(lines)

    # ═══════════════════════════════════════════════════════════════
    # YARDIMCI (PRİVATE) METOTLAR
    # ═══════════════════════════════════════════════════════════════

    def _initialize(self, w, h, timestamp):
        """İlk kare: başlangıç boyutlarını ve zamanını kaydet."""
        self.initial_w = w
        self.initial_h = h
        self.process_start_time = timestamp
        self.state_start_time = timestamp
        self.current_state = 0
        self._last_w_ratio = 1.0
        self._last_h_ratio = 1.0

    def _ratios_match(self, w_ratio, h_ratio, transition):
        """
        Verilen oranların geçiş koşullarına uyup uymadığını kontrol eder.
        KESİNLİKLE == KULLANILMAZ – hep aralık (band) kontrolü.
        """
        w_min, w_max = transition['w_ratio_range']
        h_min, h_max = transition['h_ratio_range']
        return (w_min <= w_ratio <= w_max) and (h_min <= h_ratio <= h_max)

    def _do_transition(self, w_ratio, h_ratio, timestamp):
        """Bir sonraki state'e geçişi gerçekleştirir."""
        # Mevcut state süresini kaydet
        if self.state_start_time:
            duration = (timestamp - self.state_start_time).total_seconds()
            self.state_durations[self.current_state] = duration

        # Geçiş bilgisini kaydet
        old_state = self.current_state
        self.current_state += 1
        self._confirm_count = 0
        self.state_start_time = timestamp

        step_record = {
            'name': self.STATE_NAMES.get(self.current_state, '?'),
            'from_state': old_state,
            'to_state': self.current_state,
            'timestamp': timestamp,
            'duration_seconds': self.state_durations.get(old_state, 0.0),
            'w_ratio': round(w_ratio, 3),
            'h_ratio': round(h_ratio, 3),
        }
        self.steps.append(step_record)

        # State 5'e ulaştıysa, havlunun masadan kalkmasını bekle
        # (Tamamlanma _handle_towel_lost içinde yapılır)

    def _handle_towel_lost(self, timestamp):
        """Havlu görüntüden kaybolduğunda çağrılır."""
        self._lost_count += 1
        self._confirm_count = 0

        if self._lost_count >= self.towel_lost_frames:
            if self.current_state >= 5:
                # ── BAŞARILI TAMAMLANMA ─────────────────────
                # State 5 (final katlama) sonrası havlu kalktı
                self.current_state = 6
                self.completed = True
                self.process_end_time = timestamp
                if self.state_start_time:
                    dur = (timestamp - self.state_start_time).total_seconds()
                    self.state_durations[5] = dur
            elif self.initial_w is not None:
                # ── ERKEN KAYIP – havlu tamamlanmadan kalktı ──
                self.errors.append(
                    f"Havlu State {self.current_state}'de masadan kalktı "
                    f"(tamamlanmadı)"
                )
                self.is_error = True
                self.process_end_time = timestamp

        return self.get_status()

    def _check_wrong_order(self, w_ratio, h_ratio, timestamp):
        """
        Yanlış eksenin değişip değişmediğini kontrol eder.

        Eğer mevcut state'te W değişmesi beklenirken H değişirse
        (veya tersi), 'Yanlış Sıra' hatası kaydedilir.
        """
        if self.current_state >= len(self.transitions):
            return

        transition = self.transitions[self.current_state]
        change_axis = transition['change_axis']

        # Sabit kalması gereken eksen ne kadar değişti?
        tol = self.stability_tolerance

        if change_axis == 'w':
            # W değişmeli → H sabit kalmalı
            # H'nin başlangıçtan bu yana ne kadar değiştiğini kontrol et
            # Ancak önceki state'lerde H zaten değişmiş olabilir.
            # Bu yüzden SON BİLİNEN h_ratio'ya göre karşılaştır.
            h_change = abs(h_ratio - self._last_h_ratio)
            w_change = abs(w_ratio - self._last_w_ratio)

            # H büyük değişim + W sabit → yanlış eksen değişti
            if h_change > tol and w_change < 0.05:
                msg = (f"Yanlış Sıra: State {self.current_state}'de W değişmesi "
                       f"beklenirken H değişti (h_change={h_change:.3f})")
                if msg not in self.errors:
                    self.errors.append(msg)
                    self.is_error = True

        elif change_axis == 'h':
            # H değişmeli → W sabit kalmalı
            w_change = abs(w_ratio - self._last_w_ratio)
            h_change = abs(h_ratio - self._last_h_ratio)

            if w_change > tol and h_change < 0.05:
                msg = (f"Yanlış Sıra: State {self.current_state}'de H değişmesi "
                       f"beklenirken W değişti (w_change={w_change:.3f})")
                if msg not in self.errors:
                    self.errors.append(msg)
                    self.is_error = True

    def _build_process(self):
        """Tamamlanan süreç için özet dict oluşturur (veritabanına kayıt için)."""
        end = self.process_end_time or datetime.utcnow()
        start = self.process_start_time or end
        duration = (end - start).total_seconds()
        total_steps = len(self.steps)

        # Doğru sıra: 5 geçiş yapılmış VE hata yok ise doğru katlama
        correct_fold = (total_steps >= 5) and (not self.is_error)

        return {
            'start_time': start,
            'end_time': end,
            'duration_seconds': round(duration, 2),
            'total_steps': total_steps,
            'correct_fold': correct_fold,
            'steps': self.steps,
            'state_durations': dict(self.state_durations),
            'errors': list(self.errors),
        }


# ── Geriye Uyumluluk ────────────────────────────────────────────
# main.py'de "from cv_engine.tracker import TowelStateMachine" kullanılıyor.
# Eski isimle de erişilebilsin:
TowelStateMachine = TowelTracker
