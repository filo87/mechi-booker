import logging
import os
import time
from datetime import datetime, timedelta, date
from requests import session
from urllib.parse import urljoin
from typing import List, TypedDict, Callable, Optional, Union
import pytz

MATCHI_BASE_URL = 'https://www.matchi.se'
DRY_RUN = bool(os.getenv('DRY_RUN'))


Slot = TypedDict('Slot', id=str, court=str, start=datetime,
                 end=datetime, duration=int, score=Optional[float])


class Booker:
    __slots: Optional[List[Slot]]
    __selection: Optional[Slot]

    def __init__(self, token: str, facilityId: int, on_booking=Callable[[Slot], None]):
        self.__headers = {
            'authorization': f'Basic {token}',
            'app-version': '23.1.2',
            'app-platform': 'android',
            'Host': 'www.matchi.se'
        }
        self.__facilityId = facilityId
        self.__session = session()
        self.__slots = None
        self.__selection = None
        self.__on_booking = on_booking

    def get_slots(self, target_date: date) -> 'Booker':
        '''Fetches all available slots on a given date'''
        url = urljoin(
            MATCHI_BASE_URL, f'/api/mobile/v2/secure/slots/{target_date.isoformat()}/{target_date.isoformat()}')
        params = {'facilityIds': self.__facilityId, 'sportIds': 5}
        logging.info(f'Crawling URL: {url}')
        request = self.__session.get(
            url=url, headers=self.__headers, params=params)
        response = request.json()[0]
        if len(response['restrictions']) > 0:
            raise ValueError('Still too early')
        else:
            courts = request.json()[0]['courts']
            return_slots = []
            for court in courts:
                for slot in court['slots']:
                    return_slots.append({
                        'id': slot['id'],
                        'court': court['name'],
                        'start': datetime.fromisoformat(slot['start']),
                        'end': datetime.fromisoformat(slot['end']),
                        'duration': slot['duration']
                    })
        self.__slots = return_slots
        return self

    def rank_slots(self, reference_datetime: datetime) -> 'Booker':
        '''Ranks slots based on how close they are to the target datetime, and their duration'''
        if self.__slots == None:
            raise ValueError('Requires a slot type')
        slots = self.__slots
        for slot in slots:
            score = abs(
                (reference_datetime - slot['start']).total_seconds())/60
            score += 45 - slot['duration']*0.5
            slot['score'] = score
        slots.sort(key=lambda slot: slot['score'])
        self.__slots = slots
        return self

    def print_slots(self) -> 'Booker':
        '''prints slots in a tabular format'''
        slots = self.__slots
        if len(slots) > 0:
            logging.info('Available slots:')
            for slot in slots:
                print(slot['court'][0:7], slot['start'],
                      slot['duration'], slot['score'], slot['id'], sep='\t')
        else:
            logging.info('No slots available!')
        return self

    def bookings(self) -> List[datetime]:
        url = urljoin(
            MATCHI_BASE_URL, f'/api/mobile/v2/secure/reservations')
        params = {'facilityIds': self.__facilityId, 'sportIds': 5}
        logging.info(f'Crawling URL: {url}')
        request = self.__session.get(
            url=url, headers=self.__headers, params=params)
        bookings = request.json()
        return list(map(lambda booking: datetime.fromisoformat(booking['date']), bookings))

    def __check_slot_feasibility(self, slot: Slot) -> bool:
        '''varifies if a slot fulfills the bookability criteria'''
        threshold = slot['start'] - timedelta(days=1)
        bookings = self.bookings()

        has_recent_booking = any(booking.date() >= threshold.date()
                                 for booking in bookings)
        if has_recent_booking:
            logging.warning('There is already another booking too close')
            return False

        bookings_in_same_week = list(filter(lambda booking: booking.isocalendar()[
                                     1] == slot['start'].isoformat()[1], bookings))
        if len(bookings_in_same_week) >= 2:
            logging.warning('Too many bookings that week')
            return False

        blocked_days = [1 ,6, 7]
        if slot['start'].date().isocalendar()[2] in blocked_days:
            logging.warning('Day is blocked')
            return False

        return True

    def __verify(self, slot: Slot) -> bool:
        '''varifies if a slot is still available'''
        slot_id = slot['id']
        url = urljoin(
            MATCHI_BASE_URL, f'/api/mobile/v2/secure/resources/available/slot:{slot_id}')
        logging.info(f'Crawling URL: {url}')
        request = self.__session.get(url=url, headers=self.__headers)
        return request.json()['available']

    def select(self, selector: Union[int, Callable[[Slot], bool]] = 0) -> 'Booker':
        '''selects a slot or filters multiple slots'''
        if self.__slots == None or len(self.__slots) == 0:
            self.__selection = None
        elif type(selector) is int:
            self.__selection = self.__slots[selector]
        elif callable(selector):
            self.__slots = list(filter(selector, self.__slots))
        return self

    def book(self) -> 'Booker':
        '''books the selected slot'''
        if self.__selection == None:
            logging.warning('No selected slot to book!')
            return self

        slot = self.__selection
        logging.info(
            f'Initiating booking of slot at {slot["start"]} for {slot["duration"]}min')
        if self.__check_slot_feasibility(slot) and self.__verify(slot):
            logging.info('Slot is bookable, lets go...')
            url = urljoin(MATCHI_BASE_URL, '/api/mobile/v2/secure/bookings')
            payload = {
                "payment": {
                    "method": "CREDIT_CARD_RECUR"
                },
                "playerEmails": [
                    "filo87@gmail.com"
                ],
                "slotIds": [
                    slot['id']
                ]
            }
            self.__session.post(url=url, headers=self.__headers,
                                json=payload) if not DRY_RUN else logging.warn('Dry Run! Skipping...')
            self.__on_booking(slot)
        else:
            logging.warning('Slot unfeasible or unavailable!')
        return self

    def get_best_slot_available(self, in_days: int = 14, hour: int = 19, minute: int = 00) -> 'Booker':
        target_date = (datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                       + timedelta(days=in_days)).astimezone(pytz.timezone('Europe/Zurich'))

        for i in range(30):
            try:
                self.get_slots(target_date.date())
            except ValueError:
                logging.warning(f'No slots published yet, retry {i}')
                time.sleep(2)
            else:
                break

        self.rank_slots(target_date)
        self.select(lambda slot: slot['score'] < 100 and slot['duration'] > 30)
        self.print_slots()
        self.select()
        self.book()
        return self
