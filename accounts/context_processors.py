from .models import ConsumerReg, Technician, AuthUser


def auth_context(request):
    username = request.session.get('username')
    role = request.session.get('role')
    is_authenticated = bool(username and role)
    
    consumer = None
    technician = None
    
    if is_authenticated:
        if role == 'Consumer':
            consumer = ConsumerReg.objects.filter(email=username).first()
        elif role == 'Technician':
            technician = Technician.objects.filter(Email=username).first()
            if not technician:
                technician = Technician.objects.filter(Mob=username).first()

    return {
        'session_username': username,
        'session_role': role,
        'is_authenticated_custom': is_authenticated,
        'session_consumer': consumer,
        'session_technician': technician,
    }
