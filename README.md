# Hotel Booking & Online Services Backend

A robust backend API for managing hotel bookings, customer accounts, payments, and online hotel services.
 This project provides secure and scalable fast APIs that power hotel management systems and online booking platforms.

## Features

### Authentication & Authorization
- User registration and login
- Firebase authentication
- Password  and security
- Role-based access control (Admin, Staff, Customer)

### Hotel Management
- Manage hotel information and amenities
- Hotel availability management

### Room Management
- Room categorization (Single, Double, Deluxe, Suite)
- Room pricing management
- Room availability tracking

### Booking Management
- Create room reservations
- Check room availability
- Booking history

### Online Services
- Room service requests
- Service status tracking

### Payment Processing
- Secure payment integration
- Booking payment management


## Installation

```bash
git clone https://github.com/Ck-kosh/luxe-hotel-backend.git
cd hotel-booking-backend

python3 -m venv venv

source venv/bin/activate  

pip install -r requirements.txt
```

## API Endpoints

### Authentication
- POST /api/auth/register/
- POST /api/auth/login/
- POST /api/auth/logout/

## The API will be available at:
''' bash

http://localhost:8000/

### Hotels
- GET /api/hotels/
- POST /api/hotels/

### Rooms
- GET /api/rooms/
- POST /api/rooms/


### Bookings
- GET /api/bookings/
- POST /api/bookings/
- PUT /api/bookings/:id
- DELETE /api/bookings/:id

## License

This project is not licenced
 
## Conttributors

- Elias 
- Joshua
- Fidelis
- George