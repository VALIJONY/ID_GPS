import json
from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Bugalteriya, CustomUser, DasturiyTaminot, MashinaMalumoti, Note, Rasxod, Sklad, Sotish


class BaseTestCase(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create(
            username='admin', password='admin123', firstname='Ali', last_name='Valiyev',
            is_staff=True, is_superuser=True,
        )
        self.user = CustomUser.objects.create(username='xodim', password='xodim123', firstname='Vali')
        self.soft = DasturiyTaminot.objects.create(dasturiy_taminot_nomi='Wialon')
        self.gps1 = self.make_gps('GPS-1')
        self.gps2 = self.make_gps('GPS-2')
        self.client.force_login(self.admin)

    def make_gps(self, gps_id, sold=False):
        return Sklad.objects.create(gps_id=gps_id, olingan_odam='Diler', tel_raqam='+998901112233',
                                    summa_prixod=100000, olingan_sana=date.today(), sotildi_sotilmadi=sold)

    def sale_payload(self, **extra):
        data = {
            'mijoz': 'Trans Logistic', 'mijoz_tel_raqam': '+998901234567', 'sana': date.today().isoformat(),
            'dasturiy_taminot': self.soft.id, 'username': 'trans', 'password': 'secret',
            'master': 'Usta Karim', 'master_summasi': '50 000', 'abonent_tulov': '30 000',
            'summasi': '1 000 000', 'naqd': '600 000', 'bank_schot': '100 000',
            'gps_id': [self.gps1.id, self.gps2.id], 'sim_karta': ['901', '902'],
            'mashina_turi': ['Cobalt', 'Damas'], 'davlat_raqami': ['01a777aa', '01B888BB'],
        }
        data.update(extra)
        return data


class AuthTests(BaseTestCase):
    def test_pages_require_login(self):
        self.client.logout()
        for name in ['home', 'sklad-list', 'sotish_list', 'sotish_add', 'mijozlar', 'statistika', 'bugalteriya', 'filter-sklad']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)

    def test_login_page_and_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'admin123'})
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(response.cookies['access_token']['httponly'])

    def test_hodim_pages_require_staff(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse('hodim-list')), reverse('home'))

    def test_all_pages_render(self):
        for name in ['home', 'sklad-list', 'skladadd', 'sotish_list', 'sotish_add', 'mijozlar', 'statistika',
                     'bugalteriya', 'rasxod_list', 'rasxod_add', 'hodim-list', 'hodim-create', 'note-list', 'note-add']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_bad_year_param_does_not_crash(self):
        self.assertEqual(self.client.get(reverse('statistika') + '?year=abc').status_code, 200)
        self.assertEqual(self.client.get(reverse('bugalteriya') + '?yil=abc').status_code, 200)


class SkladTests(BaseTestCase):
    def test_add_many_gps_with_formatted_price(self):
        response = self.client.post(reverse('skladadd'), {
            'gps_id': ['A1', 'A2', ' ', 'A3'], 'olingan_odam': 'Diler', 'tel_raqam': '123',
            'summa_prixod': '120 000', 'olingan_sana': date.today().isoformat(),
        })
        self.assertRedirects(response, reverse('sklad-list'))
        self.assertEqual(Sklad.objects.filter(gps_id__in=['A1', 'A2', 'A3'], summa_prixod=120000).count(), 3)

    def test_duplicate_gps_rejected(self):
        response = self.client.post(reverse('skladadd'), {
            'gps_id': ['NEW', 'GPS-1'], 'olingan_odam': 'Diler', 'tel_raqam': '123',
            'summa_prixod': '1', 'olingan_sana': date.today().isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Sklad.objects.filter(gps_id='NEW').exists())

    def test_delete_requires_post_and_superuser(self):
        url = reverse('sklad_delete', args=[self.gps1.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.force_login(self.user)
        self.client.post(url)
        self.assertTrue(Sklad.objects.filter(id=self.gps1.id).exists())
        self.client.force_login(self.admin)
        self.client.post(url)
        self.assertFalse(Sklad.objects.filter(id=self.gps1.id).exists())

    def test_sold_gps_cannot_be_deleted(self):
        sold = self.make_gps('SOLD', sold=True)
        self.client.post(reverse('sklad_delete', args=[sold.id]))
        self.assertTrue(Sklad.objects.filter(id=sold.id).exists())

    def test_filter_and_export(self):
        self.make_gps('S1', sold=True)
        response = self.client.get(reverse('sklad-list') + '?status=sold')
        self.assertEqual([i.gps_id for i in response.context['skladlist']], ['S1'])
        export = self.client.get(reverse('sklad-list') + '?export=1')
        self.assertIn('spreadsheetml', export['Content-Type'])


class SotishTests(BaseTestCase):
    def test_create_sale_marks_gps_sold_and_computes_debt(self):
        response = self.client.post(reverse('sotish_add'), self.sale_payload())
        self.assertRedirects(response, reverse('sotish_list'))
        sale = Sotish.objects.get()
        self.assertEqual((sale.summasi, sale.naqd, sale.bank_schot, sale.karta), (1000000, 600000, 100000, 300000))
        self.assertEqual(sale.abonent_tulov, 30000)
        self.assertEqual(sale.sim_karta, '901, 902')
        self.assertEqual(sale.gps_id.count(), 2)
        self.assertFalse(Sklad.objects.filter(sotildi_sotilmadi=False).exists())
        self.assertEqual(set(MashinaMalumoti.objects.values_list('davlat_raqami', flat=True)), {'01A777AA', '01B888BB'})

    def test_overpayment_rejected(self):
        response = self.client.post(reverse('sotish_add'), self.sale_payload(naqd='2 000 000'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Sotish.objects.exists())
        self.assertEqual(len(response.context['rows']), 2)  # kiritilgan qatorlar yo'qolmaydi

    def test_duplicate_gps_in_sale_rejected(self):
        payload = self.sale_payload(gps_id=[self.gps1.id, self.gps1.id])
        self.assertEqual(self.client.post(reverse('sotish_add'), payload).status_code, 200)
        self.assertFalse(Sotish.objects.exists())

    def test_update_swaps_gps_and_delete_returns_stock(self):
        self.client.post(reverse('sotish_add'), self.sale_payload(
            gps_id=[self.gps1.id], sim_karta=['901'], mashina_turi=['Cobalt'], davlat_raqami=['01A']))
        sale = Sotish.objects.get()
        edit = self.client.get(reverse('sotish_update', args=[sale.id]))
        self.assertEqual(edit.context['rows'][0]['gps_id'], str(self.gps1.id))

        self.client.post(reverse('sotish_update', args=[sale.id]), self.sale_payload(
            gps_id=[self.gps2.id], sim_karta=['902'], mashina_turi=['Damas'], davlat_raqami=['01B']))
        self.gps1.refresh_from_db(); self.gps2.refresh_from_db()
        self.assertFalse(self.gps1.sotildi_sotilmadi)
        self.assertTrue(self.gps2.sotildi_sotilmadi)

        self.client.post(reverse('sotish_delete', args=[sale.id]))
        self.gps2.refresh_from_db()
        self.assertFalse(self.gps2.sotildi_sotilmadi)
        self.assertFalse(Sotish.objects.exists())

    def test_mijozlar_and_export(self):
        self.client.post(reverse('sotish_add'), self.sale_payload())
        response = self.client.get(reverse('mijozlar'))
        self.assertEqual(response.context['device_count'], 2)
        self.assertEqual(response.context['clients'][0]['jami_summa'], 1000000 + 50000 + 30000 * 2)
        self.assertIn('spreadsheetml', self.client.get(reverse('mijozlar') + '?export=1')['Content-Type'])


class BugalteriyaTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.post(reverse('sotish_add'), self.sale_payload())
        self.sale = Sotish.objects.get()

    def toggle(self, **data):
        body = {'sotish_id': self.sale.id, 'gps_id': self.gps1.id, 'oy': 'Yanvar', 'yil': date.today().year, 'type': 'abonent'}
        body.update(data)
        return self.client.post(reverse('update_bugalteriya'), json.dumps(body), content_type='application/json').json()

    def test_state_cycle(self):
        first = self.toggle()
        self.assertEqual((first['abonent_state'], first['sim_state']), ('unpaid', 'unpaid'))
        self.assertEqual(self.toggle(tolov_id=first['tolov_id'])['abonent_state'], 'paid')
        self.assertEqual(self.toggle(tolov_id=first['tolov_id'])['abonent_state'], 'null')
        # Oddiy foydalanuvchi Null holatni o'zgartira olmaydi
        self.client.force_login(self.user)
        self.assertFalse(self.toggle(tolov_id=first['tolov_id'])['status'])
        self.client.force_login(self.admin)
        self.assertEqual(self.toggle(tolov_id=first['tolov_id'])['abonent_state'], 'unpaid')
        self.assertEqual(Bugalteriya.objects.count(), 1)

    def test_invalid_month_rejected(self):
        self.assertFalse(self.toggle(oy='Nomalum')['status'])

    def test_statistika_cumulative_counts(self):
        response = self.client.get(reverse('statistika'))
        months = response.context['months']
        current = months[date.today().month - 1]
        self.assertEqual(current['qoshilgan'], 2)
        self.assertEqual(current['jami_aktiv'], current['oldingi_aktiv'] + current['qoshilgan'])


class RasxodHodimNoteTests(BaseTestCase):
    def test_rasxod_create_and_update_with_formatted_sum(self):
        self.client.post(reverse('rasxod_add'), {'rasxod_nomi': 'Ijara', 'sana': date.today().isoformat(), 'summa': '2 500 000'})
        rasxod = Rasxod.objects.get()
        self.assertEqual(rasxod.summa, 2500000)
        response = self.client.post(reverse('rasxod_update', args=[rasxod.id]),
                                    {'rasxod_nomi': 'Ijara', 'sana': date.today().isoformat(), 'summa': '3 000 000'})
        self.assertRedirects(response, reverse('rasxod_list'))
        rasxod.refresh_from_db()
        self.assertEqual(rasxod.summa, 3000000)

    def test_hodim_update_keeps_password_when_blank(self):
        old_hash = self.user.password
        self.client.post(reverse('hodim-update', args=[self.user.id]), {
            'firstname': 'Yangi', 'last_name': 'Ism', 'position': 'Xodim', 'username': 'xodim', 'password': '',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.firstname, 'Yangi')
        self.assertEqual(self.user.password, old_hash)
        self.assertTrue(self.user.check_password('xodim123'))

    def test_cannot_delete_self(self):
        self.client.post(reverse('hodim-delete', args=[self.admin.id]))
        self.assertTrue(CustomUser.objects.filter(id=self.admin.id).exists())

    def test_note_uses_today(self):
        self.client.post(reverse('note-add'), {'note': 'Salom'})
        self.assertEqual(Note.objects.get().sana, date.today())
