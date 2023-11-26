# Mechi-Booker

Mechi-Booker is a Python project designed to automate the regular booking of padel courts. With Mechi-Booker, you can easily schedule padel court bookings in advance, saving you time and ensuring you never miss a game.

## Installation

Make sure you have Python 3 installed on your system. If not, you can download it from [python.org](https://www.python.org/downloads/).

To manage project dependencies, Mechi-Booker uses Pipenv. If you don't have Pipenv installed, you can install it using:

```bash
pip install pipenv
```

Clone the Mechi-Booker repository to your local machine:

```bash
git clone https://github.com/your-username/mechi-booker.git
```

Navigate to the project directory:

```bash
cd mechi-booker
```

Install project dependencies using Pipenv:

```bash
pipenv install
```

Copy the `.env.example` file and create a new `.env` file:

```bash
cp .env.example .env
```

Edit the `.env` file and provide the necessary configuration parameters.

## Usage

Activate the virtual environment:

```bash
pipenv shell
```

Run the Mechi-Booker script:

```bash
python mechi_booker.py
```

Mechi-Booker will prompt you for the required information to book a padel court. Follow the prompts and let Mechi-Booker handle the booking process for you.

## Docker Compose

Mechi-Booker also includes a Docker Compose configuration for easy deployment. Ensure you have Docker and Docker Compose installed on your system.

To build and run Mechi-Booker with Docker Compose:

```bash
docker-compose up --build
```

This will build the Docker image and start the Mechi-Booker container.

## Configuration

The configuration options for Mechi-Booker are set in the `.env` file. Make sure to provide the required information such as login credentials, booking details, etc.

## License

This project is licensed under the GPL3 License.

Feel free to contribute to this project by submitting issues or pull requests. Happy padel playing with Mechi-Booker!