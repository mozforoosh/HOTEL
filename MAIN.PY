# ---------------- Task 1: Rooms ----------------
class Room:
    def __init__(self, room_number, price, capacity):
        self.room_number = room_number
        self.price = price          
        self.capacity = capacity
        self.is_booked = False

    def book(self):
        self.is_booked = True

    def release(self):
        self.is_booked = False

    def nightly_price(self):
        return self.price

    def __str__(self):
        status = "booked" if self.is_booked else "empty"
        return (f"{self.__class__.__name__} | number={self.room_number} | "
                f"price={self.nightly_price()} | capacity={self.capacity} | {status}")


class StandardRoom(Room):
    pass


class SuiteRoom(Room):
    def __init__(self, room_number, price, capacity, amenities=None, service_cost=0):
        super().__init__(room_number, price, capacity)
        self.amenities = amenities or []
        self.service_cost = service_cost   

    def nightly_price(self):
        return self.price + self.service_cost


# ---------------- Task 2: Guests ----------------
class Guest:
    MAX_RESERVATIONS = 2
    DISCOUNT = 0.0

    def __init__(self, guest_id, name):
        self.guest_id = guest_id
        self.name = name
        self.reservations = []   

    def can_reserve(self):
        
        return len(self.reservations) < self.MAX_RESERVATIONS

    def add_reservation(self, room_number):
        if not self.can_reserve():
            return (f"Sorry {self.name}, you have reached the maximum of "
                    f"{self.MAX_RESERVATIONS} reservations.")
        if room_number in self.reservations:
            return f"Dear {self.name}, you have already reserved room {room_number}."
        self.reservations.append(room_number)
        return f"Room {room_number} was added to the reservations of {self.name}."

    def cancel_reservation(self, room_number):
        if room_number not in self.reservations:
            return f"Dear {self.name}, you have no reservation for room {room_number}."
        self.reservations.remove(room_number)
        return f"Room {room_number} was removed from the reservations of {self.name}."

    def get_discount(self):
        return self.DISCOUNT

    def late_penalty(self, nightly_price):
        return 0.0   

    def __str__(self):
        return (f"{self.__class__.__name__} | id={self.guest_id} | name={self.name} "
                f"| reservations={self.reservations}")


class NormalGuest(Guest):
    MAX_RESERVATIONS = 2
    DISCOUNT = 0.0


class VIPGuest(Guest):
    MAX_RESERVATIONS = 5
    DISCOUNT = 0.10        
    PENALTY_RATE = 0.20    

    def late_penalty(self, nightly_price):
        return round(nightly_price * self.PENALTY_RATE, 2)



class Reservation:
    def __init__(self, guest, room, people, nights, extra_services=0):
        self.guest = guest
        self.room = room
        self.people = people
        self.nights = nights
        self.extra_services = extra_services
        self.checked_in = False


class Hotel:
    def __init__(self, name):
        self.name = name
        self.rooms = {}      
        self.guests = {}   
        self.reservations = {}   

    # ----- Task 3: register and look up -----
    def add_room(self, room):
        if room.room_number in self.rooms:
            return f"Room {room.room_number} already exists in the hotel."
        self.rooms[room.room_number] = room
        return f"Room {room.room_number} was added to {self.name}."

    def add_guest(self, guest):
        if guest.guest_id in self.guests:
            return f"A guest with ID {guest.guest_id} is already registered."
        self.guests[guest.guest_id] = guest
        return f"Welcome {guest.name}! You are registered with ID {guest.guest_id}."

    def find_empty_room(self, people=1):
        for room in self.rooms.values():
            if not room.is_booked and room.capacity >= people:
                return f"An empty room is available for {people} people: {room}"
        return f"Sorry, no empty room is available for {people} people."

    def get_room_info(self, room_number):
        room = self.rooms.get(room_number)
        if room is None:
            return f"Sorry, room {room_number} does not exist."
        return str(room)

    def get_guest_info(self, guest_id):
        guest = self.guests.get(guest_id)
        if guest is None:
            return f"Sorry, we could not find a guest with ID {guest_id}."
        return str(guest)

    # ----- Task 5: cost (a calculation, so it returns a number) -----
    def calculate_cost(self, room, nights, extra_services, guest):
        room_cost = room.nightly_price() * nights
        discount = room_cost * guest.get_discount()   
        return round(room_cost + extra_services - discount, 2)

    # ----- Task 4: reserve / cancel / check-in / check-out -----
    def reserve(self, guest_id, room_number, people, nights, extra_services=0):
        guest = self.guests.get(guest_id)
        room = self.rooms.get(room_number)
        if guest is None:
            return f"Sorry, we could not find a guest with ID {guest_id}."
        if room is None:
            return f"Sorry, room {room_number} does not exist."
        if nights < 1:
            return "The number of nights must be at least 1."
        if room.is_booked:
            return f"Sorry {guest.name}, room {room_number} is already booked."
        if people > room.capacity:
            return (f"Sorry {guest.name}, room {room_number} can host at most "
                    f"{room.capacity} people, but you asked for {people}.")
        if not guest.can_reserve():
            return (f"Sorry {guest.name}, you have reached the maximum of "
                    f"{guest.MAX_RESERVATIONS} reservations.")

        guest.add_reservation(room_number)
        room.book()
        self.reservations[room_number] = Reservation(guest, room, people, nights, extra_services)
        cost = self.calculate_cost(room, nights, extra_services, guest)
        return (f"Dear {guest.name}, room {room_number} is reserved for you for "
                f"{nights} night(s). Estimated cost: {cost}.")

    def _get_own_reservation(self, guest_id, room_number):
        """Internal helper. Returns (reservation, error_text)."""
        guest = self.guests.get(guest_id)
        if guest is None:
            return None, f"Sorry, we could not find a guest with ID {guest_id}."
        res = self.reservations.get(room_number)
        if res is None:
            return None, f"Sorry {guest.name}, there is no reservation for room {room_number}."
        if res.guest.guest_id != guest_id:
            return None, f"Sorry {guest.name}, room {room_number} is reserved by another guest."
        return res, None

    def cancel(self, guest_id, room_number, late=False):
        res, error = self._get_own_reservation(guest_id, room_number)
        if error:
            return error
        if res.checked_in:
            return f"Sorry {res.guest.name}, you cannot cancel after check-in."

        penalty = res.guest.late_penalty(res.room.nightly_price()) if late else 0.0
        name = res.guest.name
        res.guest.cancel_reservation(room_number)
        res.room.release()
        del self.reservations[room_number]

        if penalty > 0:
            return (f"Dear {name}, your reservation for room {room_number} was canceled. "
                    f"A late cancellation penalty of {penalty} was applied.")
        return (f"Dear {name}, your reservation for room {room_number} was canceled. "
                f"No penalty was applied.")

    def check_in(self, guest_id, room_number):
        res, error = self._get_own_reservation(guest_id, room_number)
        if error:
            return error
        if res.checked_in:
            return f"Dear {res.guest.name}, you have already checked in to room {room_number}."
        res.checked_in = True
        return f"Welcome {res.guest.name}! You are checked in to room {room_number}. Enjoy your stay."

    def check_out(self, guest_id, room_number, late=False):
        res, error = self._get_own_reservation(guest_id, room_number)
        if error:
            return error
        if not res.checked_in:
            return f"Sorry {res.guest.name}, you have not checked in to room {room_number} yet."

        total = self.calculate_cost(res.room, res.nights, res.extra_services, res.guest)
        penalty = res.guest.late_penalty(res.room.nightly_price()) if late else 0.0
        total = round(total + penalty, 2)

        name = res.guest.name
        res.guest.cancel_reservation(room_number)
        res.room.release()
        del self.reservations[room_number]

        if penalty > 0:
            return (f"Dear {name}, check-out from room {room_number} is complete. "
                    f"Total bill: {total} (includes a late check-out penalty of {penalty}). "
                    f"Thank you for staying with us!")
        return (f"Dear {name}, check-out from room {room_number} is complete. "
                f"Total bill: {total}. Thank you for staying with us!")


# ---------------- tests ----------------
def show(title, output):
    print(f"[{title}]")
    print(output)
    print()


if __name__ == "__main__":
    hotel = Hotel("Grand Hotel")

    show("add room", hotel.add_room(StandardRoom(101, 50, 2)))
    show("add duplicate room", hotel.add_room(StandardRoom(101, 50, 2)))
    hotel.add_room(StandardRoom(102, 50, 2))
    hotel.add_room(StandardRoom(103, 50, 2))
    hotel.add_room(SuiteRoom(201, 120, 4, ["jacuzzi"], service_cost=30))
    hotel.add_room(SuiteRoom(202, 120, 4, ["jacuzzi"], service_cost=30))

    show("add guest", hotel.add_guest(NormalGuest(1, "Parsa")))
    show("add duplicate guest", hotel.add_guest(NormalGuest(1, "Parsa")))
    hotel.add_guest(VIPGuest(2, "Sara"))

    show("find room (3 people)", hotel.find_empty_room(3))
    show("find room (10 people)", hotel.find_empty_room(10))
    show("room info", hotel.get_room_info(101))
    show("guest info", hotel.get_guest_info(99))

    show("reserve ok", hotel.reserve(1, 101, 2, 2, 10))
    show("reserve booked room", hotel.reserve(2, 101, 1, 1))
    show("reserve unknown guest", hotel.reserve(99, 102, 1, 1))
    show("reserve unknown room", hotel.reserve(1, 999, 1, 1))
    show("reserve over capacity", hotel.reserve(1, 102, 5, 1))
    show("reserve second room", hotel.reserve(1, 102, 2, 1))
    show("reserve over max", hotel.reserve(1, 103, 1, 1))

    show("check-in ok", hotel.check_in(1, 101))
    show("check-in twice", hotel.check_in(1, 101))
    show("check-in wrong guest", hotel.check_in(2, 102))
    show("cancel after check-in", hotel.cancel(1, 101))
    show("normal guest late cancel", hotel.cancel(1, 102, late=True))
    show("normal guest check-out", hotel.check_out(1, 101))

    show("VIP reserve suite", hotel.reserve(2, 201, 3, 3, 40))
    show("check-out before check-in", hotel.check_out(2, 201))
    hotel.check_in(2, 201)
    show("VIP late check-out", hotel.check_out(2, 201, late=True))

    hotel.reserve(2, 202, 2, 1)
    show("VIP late cancel", hotel.cancel(2, 202, late=True))