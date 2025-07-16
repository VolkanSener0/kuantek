import time
import random
import math
from datetime import datetime
import json
import os

class SecureFHSSAlgorithm:
    """
    Frekans Atlamalı ve Fiziksel Katmanlı Güvenli Haberleşme Sistemi
    
    Bu algoritma hem gönderici hem alıcı tarafında aynı şekilde çalışır.
    Gönderici ve alıcı birbirine bağlı değil, aynı algoritmaya bağlı olarak çalışır.
    
    Gürültü toleransı için: Türkiye'den LEO uydularına (400-800 km) sinyal gönderiminde 
    gürültü oranı %0.99 . Genlik toleransı (2.7V-3.3V), zaman toleransı 
    (1.9-2.1 ms) ve 40 MHz frekans toleransı, gürültüyü tolere eder.
    
    Güvenlik için: 40 MHz tolerans, 2000-4000 MHz bandında 2000 kanaldan 
    sadece %2'lik bir hedef alanı kapsar. 2 ms hızlı atlama ve şifreli, değişken 
    k₁×k₂ sırası, düşmanın sinyali taklit etmesini engellemiş olur.
    """
    
    def __init__(self, sync_key=12345):
        """
        Algoritma değerlerini başlatır
        
        Args:
            sync_key (int): Senkronizasyon anahtarı (her iki cihaz da aynı olmalı)
        """
        self.sync_key = sync_key
        
        # Algoritma değerleri (sabit değerler)
        self.f0 = 2000  # MHz - S Bandı başlangıcı
        self.t_hop = 2  # ms - Atlama süresi (sabit)
        self.band_min = 2000  # MHz - S Bandı alt limit
        self.band_max = 4000  # MHz - S Bandı üst limit
        self.nominal_amplitude = 3.0  # V - Nominal genlik
        self.amplitude_tolerance = 0.3  # V - Genlik toleransı (sabit)
        self.time_tolerance = 0.1  # ms - Zaman toleransı
        
        # Dinamik k1 * k2 listesi (1000-3000 aralığında 5 rastgele değer)
        random.seed(self.sync_key)
        self.k1_k2_list = sorted([random.randint(1000, 3000) for _ in range(5)])
        self.k2_constant = 100  # k2 sabit değer
        
        # Algoritma durumu
        self.current_k_index = 0
        self.hop_counter = 0
        
        # Senkronizasyon için seed sıfırla
        random.seed(self.sync_key)
        
        print("FREKANS ATLAMALI VE FİZİKSEL KATMANLI GÜVENLİ HABERLEŞME ALGORİTMASI")
        print(f"Senkronizasyon anahtarı: {sync_key}")
        print(f"Çalışma bandı: {self.band_min}-{self.band_max} MHz (S Bandı)")
        print(f"Atlama süresi: {self.t_hop} ms ± {self.time_tolerance} ms")
        print(f"Nominal genlik: {self.nominal_amplitude} ± {self.amplitude_tolerance} V")
        print(f"Gürültü toleransı: %0.99 (SNR ≈ 20 dB)")
        print(f"Güvenlik: 40 MHz tolerans (~40 kanal), düşman tahmini < %2")
        print(f"Dinamik k1×k2 listesi: {self.k1_k2_list}")
        print("-" * 70)
    
    def get_k1_k2_values(self):
        """
        Şifreli katsayı listesinden k1 ve k2 değerlerini döndürür
        
        Returns:
            tuple: (k1, k2) değerleri
        """
        k1_k2_product = self.k1_k2_list[self.current_k_index % len(self.k1_k2_list)]
        k1 = k1_k2_product // self.k2_constant
        k2 = self.k2_constant
        return k1, k2
    
    def calculate_frequency(self, amplitude, time_ms, energy):
        """
        Temel algoritma: Frekans hesaplama formülü
        
        f = f₀ + (A × k₁ + E × k₂) / t
        
        Args:
            amplitude (float): Genlik (A) - Volt
            time_ms (float): Zaman (t) - milisaniye
            energy (float): Enerji (E) - A² × t
        
        Returns:
            dict: Hesaplama sonuçları
        """
        # Sıfır bölme koruması
        if time_ms <= 0:
            time_ms = self.t_hop
        
        attempts = 0
        max_attempts = len(self.k1_k2_list)
        original_k_index = self.current_k_index
        
        while attempts < max_attempts:
            # Şifreli listeden k1, k2 değerlerini al
            k1, k2 = self.get_k1_k2_values()
            
            # Temel Formül: f = f₀ + (A × k₁ + E × k₂) / t
            try:
                frequency = self.f0 + (amplitude * k1 + energy * k2) / time_ms
            except ZeroDivisionError:
                frequency = self.f0
            
            # S Bandı kontrolü ve düzeltme
            if frequency < self.band_min:
                frequency = self.band_min
            elif frequency > self.band_max:
                frequency = self.band_max
                
            if self.band_min <= frequency <= self.band_max:
                result = {
                    'frequency': frequency,
                    'amplitude': amplitude,
                    'time_ms': time_ms,
                    'energy': energy,
                    'k1': k1,
                    'k2': k2,
                    'k1_k2_product': k1 * k2,
                    'k_index': self.current_k_index,
                    'formula': f"f = {self.f0} + ({amplitude:.2f} × {k1} + {energy:.2f} × {k2}) / {time_ms}",
                    'calculation': f"f = {self.f0} + ({amplitude * k1:.1f} + {energy * k2:.1f}) / {time_ms}",
                    'is_valid': True,
                    'attempts': attempts + 1
                }
                return result
            
            # Eğer bant dışındaysa, listedeki bir sonraki k1×k2 değerini dene
            self.current_k_index = (self.current_k_index + 1) % len(self.k1_k2_list)
            attempts += 1
        
        # Eğer hiçbiri bir işe yaramazsa (çok nadir bir durum)
        self.current_k_index = original_k_index
        return {
            'frequency': self.f0,
            'amplitude': amplitude,
            'time_ms': time_ms,
            'energy': energy,
            'k1': 10,
            'k2': 100,
            'k1_k2_product': 1000,
            'k_index': self.current_k_index,
            'formula': f"FALLBACK: f = {self.f0} (bant dışı)",
            'calculation': f"FALLBACK: f = {self.f0}",
            'is_valid': False,
            'attempts': max_attempts
        }
    
    def generate_signal_parameters(self):
        """
        Gönderici için: Sinyal değerlerini üretir
        
        Returns:
            dict: Üretilen sinyal değerleri
        """
        # Genlik üretimi: 3V ± 0.15V aralığında (daha dar)
        amplitude = self.nominal_amplitude + random.uniform(-0.15, 0.15)
        
        # Zaman sabit: 2 ms
        time_ms = self.t_hop
        
        # Enerji hesaplama: E = A² × t
        energy = amplitude ** 2 * time_ms
        
        return {
            'amplitude': amplitude,
            'time_ms': time_ms,
            'energy': energy,
            'generation_method': 'sender_generated'
        }
    
    def measure_signal_parameters(self, received_amplitude, received_energy, received_time):
        """
        Alıcı için: Gelen sinyalin değerlerini ölçer
        
        Args:
            received_amplitude (float): Alınan genlik
            received_energy (float): Alınan enerji
            received_time (float): Alınan zaman
        
        Returns:
            dict: Ölçülen sinyal değerleri
        """
        return {
            'amplitude': received_amplitude,
            'time_ms': received_time,
            'energy': received_energy,
            'generation_method': 'receiver_measured'
        }
    
    def validate_signal(self, amplitude, time_ms):
        """
        Sinyal doğruluğunu kontrol eder
        
        Args:
            amplitude (float): Kontrol edilecek genlik
            time_ms (float): Kontrol edilecek zaman
        
        Returns:
            dict: Doğrulama sonucu
        """
        min_amplitude = self.nominal_amplitude - self.amplitude_tolerance
        max_amplitude = self.nominal_amplitude + self.amplitude_tolerance
        min_time = self.t_hop - self.time_tolerance
        max_time = self.t_hop + self.time_tolerance
        
        is_valid_amplitude = min_amplitude <= amplitude <= max_amplitude
        is_valid_time = min_time <= time_ms <= max_time
        
        is_valid = is_valid_amplitude and is_valid_time
        
        return {
            'is_valid': is_valid,
            'is_valid_amplitude': is_valid_amplitude,
            'is_valid_time': is_valid_time,
            'amplitude': amplitude,
            'time_ms': time_ms,
            'min_allowed_amplitude': min_amplitude,
            'max_allowed_amplitude': max_amplitude,
            'min_allowed_time': min_time,
            'max_allowed_time': max_time,
            'tolerance_amplitude': self.amplitude_tolerance,
            'tolerance_time': self.time_tolerance
        }
    
    def sync_check(self):
        """
        Her 100 hop iletiminde bir senkronizasyon kontrolü yapar
        
        Returns:
            dict: Senkronizasyon durumu
        """
        if self.hop_counter % 100 == 0 and self.hop_counter > 0:
            return {
                'sync_needed': True,
                'hop_count': self.hop_counter,
                'reference_freq': 2750,  # MHz
                'test_amplitude': self.nominal_amplitude,
                'test_duration': 5,  # ms
                'message': f"Senkronizasyon kontrolü #{self.hop_counter // 100}"
            }
        return {
            'sync_needed': False,
            'hop_count': self.hop_counter
        }
    
    def next_hop(self):
        """
        Bir sonraki hop için algoritma durumunu günceller
        """
        self.hop_counter += 1
        self.current_k_index = (self.current_k_index + 1) % len(self.k1_k2_list)
        
        return {
            'hop_counter': self.hop_counter,
            'k_index': self.current_k_index,
            'next_k1_k2': self.k1_k2_list[self.current_k_index % len(self.k1_k2_list)]
        }
    
    def simulate_sender_operation(self, hop_count=10):
        """
        Gönderici simülasyonu: Teorik gönderici işlemi
        
        Args:
            hop_count (int): Simüle edilecek hop sayısı
        
        Returns:
            list: Gönderici işlem sonuçları
        """
        results = []
        
        print(f"Gönderici simülasyonu - {hop_count} hop")
        print("-" * 50)
        
        for i in range(hop_count):
            # Sinyal değerlerini üret
            params = self.generate_signal_parameters()
            
            # Frekansı hesapla
            freq_result = self.calculate_frequency(
                params['amplitude'], 
                params['time_ms'], 
                params['energy']
            )
            
            # Senkronizasyon kontrolü
            sync_result = self.sync_check()
            
            # Sonuçları birleştir
            result = {
                'hop_number': i + 1,
                'timestamp': datetime.now().isoformat(),
                'operation': 'sender',
                **params,
                **freq_result,
                'sync_info': sync_result
            }
            
            results.append(result)
            
            # Konsol çıktısı
            status = "GECERLI" if freq_result['is_valid'] else "GECERSIZ"
            print(f"Hop #{i+1:02d} {status} | "
                  f"A:{params['amplitude']:.2f}V | "
                  f"E:{params['energy']:.1f} | "
                  f"f:{freq_result['frequency']:.1f}MHz | "
                  f"k1×k2:{freq_result['k1_k2_product']}")
            
            if sync_result['sync_needed']:
                print(f"        {sync_result['message']}")
            
            # Bir sonraki hop'a geç
            self.next_hop()
            
            # Kısa bekleme (simülasyon için)
            time.sleep(0.001)
        
        return results
    
    def simulate_receiver_operation(self, sender_results, noise_level=0.0099):
        """
        Alıcı simülasyonu: Teorik alıcı işlemi
        
        Args:
            sender_results (list): Gönderici sonuçları
            noise_level (float): Gürültü seviyesi (0.0099 = %0.99, SNR ≈ 20 dB)
        
        Returns:
            list: Alıcı işlem sonuçları
        """
        results = []
        
        print(f"\nAlıcı simülasyonu - {len(sender_results)} hop")
        print(f"Gürültü seviyesi: %{noise_level*100:.2f} (SNR ≈ 20 dB)")
        print("-" * 50)
        
        # Algoritma durumunu sıfırla (aynı algoritmayı kullanacak)
        self.current_k_index = 0
        self.hop_counter = 0
        
        for i, sender_data in enumerate(sender_results):
            # Gürültülü sinyal simülasyonu
            noise_factor = 1 + random.uniform(-noise_level, noise_level)
            
            received_amplitude = sender_data['amplitude'] * noise_factor
            received_energy = sender_data['energy'] * noise_factor
            received_time = sender_data['time_ms'] + random.uniform(-0.05, 0.05)
            
            # Sinyal değerlerini ölç
            measured_params = self.measure_signal_parameters(
                received_amplitude, received_energy, received_time
            )
            
            # Sinyal doğruluğunu kontrol et
            validation = self.validate_signal(measured_params['amplitude'], measured_params['time_ms'])
            
            if validation['is_valid']:
                # AYNI ALGORİTMAYI kullanarak frekansı hesapla
                freq_result = self.calculate_frequency(
                    measured_params['amplitude'],
                    measured_params['time_ms'],
                    measured_params['energy']
                )
                
                # Orijinal frekansla karşılaştır
                freq_difference = abs(freq_result['frequency'] - sender_data['frequency'])
                is_match = freq_difference < 40.0  # 40 MHz tolerans
                status = "KABUL" if is_match else "REDDEDILDI"
                
                print(f"Hop #{i+1:02d} {status} | "
                      f"A:{measured_params['amplitude']:.2f}V | "
                      f"t:{measured_params['time_ms']:.2f}ms | "
                      f"f:{freq_result['frequency']:.1f}MHz | "
                      f"Δf:{freq_difference:.1f}MHz")
                
            else:
                freq_result = {'frequency': 0, 'is_valid': False}
                freq_difference = float('inf')
                is_match = False
                
                reason = "Genlik tolerans dışı" if not validation['is_valid_amplitude'] else "Zaman tolerans dışı"
                print(f"Hop #{i+1:02d} REDDEDILDI | "
                      f"A:{measured_params['amplitude']:.2f}V | "
                      f"t:{measured_params['time_ms']:.2f}ms | "
                      f"SİNYAL REDDEDİLDİ ({reason})")
            
            # Senkronizasyon kontrolü
            sync_result = self.sync_check()
            
            # Sonuçları birleştir
            result = {
                'hop_number': i + 1,
                'timestamp': datetime.now().isoformat(),
                'operation': 'receiver',
                'original_data': sender_data,
                **measured_params,
                'validation': validation,
                'freq_result': freq_result,
                'frequency_difference': freq_difference,
                'is_match': is_match,
                'sync_info': sync_result
            }
            
            results.append(result)
            
            if sync_result['sync_needed']:
                print(f"        {sync_result['message']}")
            
            # Bir sonraki hop'a geç
            self.next_hop()
            
            # Kısa bekleme (simülasyon için)
            time.sleep(0.001)
        
        return results
    
    def calculate_statistics(self, sender_results, receiver_results):
        """
        İstatistik hesaplama
        
        Args:
            sender_results (list): Gönderici sonuçları
            receiver_results (list): Alıcı sonuçları
        
        Returns:
            dict: İstatistikler
        """
        # Gönderici istatistikleri
        sender_frequencies = [r['frequency'] for r in sender_results if r.get('is_valid', False)]
        sender_stats = {
            'total_hops': len(sender_results),
            'valid_hops': len(sender_frequencies),
            'avg_frequency': sum(sender_frequencies) / len(sender_frequencies) if sender_frequencies else 0,
            'min_frequency': min(sender_frequencies) if sender_frequencies else 0,
            'max_frequency': max(sender_frequencies) if sender_frequencies else 0,
            'frequency_range': max(sender_frequencies) - min(sender_frequencies) if sender_frequencies else 0
        }
        
        # Alıcı istatistikleri
        valid_receptions = [r for r in receiver_results if r.get('validation', {}).get('is_valid', False)]
        successful_matches = [r for r in valid_receptions if r.get('is_match', False)]
        
        # Gürültü oranı ve SNR tahmini
        noise_percentage = 0.99  # %0.99 (SNR ≈ 20 dB)
        estimated_snr = 10 * math.log10(1 / (noise_percentage / 100))
        
        receiver_stats = {
            'total_receptions': len(receiver_results),
            'valid_receptions': len(valid_receptions),
            'successful_matches': len(successful_matches),
            'success_rate': (len(successful_matches) / len(receiver_results) * 100) if receiver_results else 0,
            'validation_rate': (len(valid_receptions) / len(receiver_results) * 100) if receiver_results else 0,
            'noise_percentage': noise_percentage,
            'estimated_snr_db': estimated_snr
        }
        
        return {
            'sender': sender_stats,
            'receiver': receiver_stats
        }
    
    def export_results(self, sender_results, receiver_results, filename=None):
        """
        Sonuçları JSON dosyasına kaydet
        
        Args:
            sender_results (list): Gönderici sonuçları
            receiver_results (list): Alıcı sonuçları
            filename (str): Dosya adı
        
        Returns:
            str: Kaydedilen dosya adı
        """
        if not filename:
            filename = f"fhss_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            data = {
                'algorithm_info': {
                    'name': 'Frekans Atlamalı ve Fiziksel Katmanlı Güvenli Haberleşme Sistemi',
                    'sync_key': self.sync_key,
                    'parameters': {
                        'f0': self.f0,
                        't_hop': self.t_hop,
                        'band_range': [self.band_min, self.band_max],
                        'amplitude_nominal': self.nominal_amplitude,
                        'amplitude_tolerance': self.amplitude_tolerance,
                        'time_tolerance': self.time_tolerance,
                        'k1_k2_list': self.k1_k2_list,
                        'noise_level': 0.0099,  # %0.99 (SNR ≈ 20 dB)
                        'estimated_snr_db': 10 * math.log10(1 / 0.0099),
                        'freq_tolerance': 40.0  # MHz
                    }
                },
                'sender_results': sender_results,
                'receiver_results': receiver_results,
                'statistics': self.calculate_statistics(sender_results, receiver_results)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Sonuçlar kaydedildi: {filename}")
            return filename
            
        except Exception as e:
            print(f"Dosya kaydetme hatası: {e}")
            return None


# Örnek çalışma
def main():
    """Ana fonksiyon"""
    try:
        print("TEKNOFEST 2025 - GÜVENLİ UYDU HABERLEŞME SİSTEMİ")
        print("=" * 70)
        print("Teorik Proje - Algoritma Simülasyonu")
        print("=" * 70)
        
        # Algoritma oluştur
        algorithm = SecureFHSSAlgorithm(sync_key=12345)
        
        # Gönderici simülasyonu
        print("\nGÖNDERİCİ SİMÜLASYONU BAŞLATILIYOR...")
        sender_results = algorithm.simulate_sender_operation(hop_count=15)
        
        # Alıcı simülasyonu (aynı algoritma)
        print("\nALICI SİMÜLASYONU BAŞLATILIYOR...")
        receiver_results = algorithm.simulate_receiver_operation(sender_results, noise_level=0.0099)
        
        # İstatistikler
        stats = algorithm.calculate_statistics(sender_results, receiver_results)
        
        print("\nSİMÜLASYON İSTATİSTİKLERİ:")
        print("-" * 40)
        print(f"Gönderici:")
        print(f"   • Toplam hop: {stats['sender']['total_hops']}")
        print(f"   • Geçerli hop: {stats['sender']['valid_hops']}")
        print(f"   • Ortalama frekans: {stats['sender']['avg_frequency']:.1f} MHz")
        print(f"   • Frekans aralığı: {stats['sender']['frequency_range']:.1f} MHz")
        
        print(f"\nAlıcı:")
        print(f"   • Toplam alım: {stats['receiver']['total_receptions']}")
        print(f"   • Geçerli alım: {stats['receiver']['valid_receptions']}")
        print(f"   • Başarılı eşleşme: {stats['receiver']['successful_matches']}")
        print(f"   • Başarı oranı: {stats['receiver']['success_rate']:.1f}%")
        print(f"   • Gürültü oranı: {stats['receiver']['noise_percentage']:.2f}%")
        print(f"   • Tahmini SNR: {stats['receiver']['estimated_snr_db']:.1f} dB")
        
        # Sonuçları kaydet
        saved_file = algorithm.export_results(sender_results, receiver_results)
        
        if saved_file:
            print("\nSİMÜLASYON BAŞARIYLA TAMAMLANDI!")
            print("Algoritma hem gönderici hem alıcı tarafında çalıştı!")
        else:
            print("\nSimülasyon tamamlandı ama dosya kaydedilemedi!")
            
    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()