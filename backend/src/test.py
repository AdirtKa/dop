"""Служебный CLI-скрипт для ручного создания пользователя."""

import asyncio
import getpass

from sqlalchemy import select

from src.session import async_session
from src.models.user import User, UserRole
from src.routes.auth.security import get_password_hash


async def main() -> None:
    """Создаёт пользователя через консольный ввод."""
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()

    print("Role:")
    print("1 - employee")
    print("2 - admin")
    print("3 - organization")

    role_choice = input("Choose role: ").strip()

    roles = {
        "1": UserRole.EMPLOYEE,
        "2": UserRole.ADMIN,
        "3": UserRole.ORGANIZATION,
    }

    role = roles.get(role_choice)

    if role is None:
        print("Invalid role")
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user is not None:
            print("User already exists")
            return

        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=role,
            is_active=True,
        )

        session.add(user)
        await session.commit()

        print("User created successfully")
        print(f"Username: {username}")
        print(f"Role: {role.value}")


if __name__ == "__main__":
    asyncio.run(main())
