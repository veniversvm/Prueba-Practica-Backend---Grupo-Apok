from rest_framework import serializers
from django.contrib.auth import get_user_model
from nodes.models import Node  # Importación necesaria para auditoría

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer base para operaciones de lectura (GET) y actualización (PUT/PATCH).

    Características:
    - Permite actualizaciones parciales sin exigir 'email' o 'username' obligatoriamente.
    - La contraseña es 'write_only' (nunca se lee, solo se escribe).
    - Incluye validaciones de unicidad personalizadas para permitir editar el propio perfil.
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text="Dejar en blanco para mantener la contraseña actual."
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_email_confirmed', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'password'
        ]
        read_only_fields = [
            'date_joined', 'last_login', 'is_staff', 'is_superuser'
        ]
        # SOLUCIÓN AL ERROR DE VALIDACIÓN EN UPDATE:
        # Establecemos required=False para permitir PATCH/PUT sin enviar estos campos.
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False}
        }

    def validate_role(self, value):
        """
        Valida que solo un usuario con rol SUDO pueda asignar el rol SUDO a otro.
        """
        request = self.context.get('request')
        if request and value == 'SUDO':
            if request.user.role != 'SUDO':
                raise serializers.ValidationError(
                    "Solo los usuarios SUDO pueden asignar el rol SUDO."
                )
        return value

    def validate_email(self, value):
        """
        Valida que el email sea único en el sistema.
        Excluye a la instancia actual de la comprobación para permitir auto-edición.
        """
        # Verificamos si existe otro usuario con este email
        # .exclude(pk=self.instance.pk) evita que falle si el usuario guarda su propio email
        query = User.objects.filter(email__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        
        return value

    def update(self, instance, validated_data):
        """
        Actualiza la instancia del usuario.
        Maneja el hash de la contraseña si se proporciona una nueva.
        """
        password = validated_data.pop('password', None)

        # Actualiza los campos estándar
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Si se envió password, se hashea y guarda
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserDetailSerializer(UserSerializer):
    """
    Serializer extendido para la vista de detalle (GET /users/{id}/).
    Incluye métricas adicionales de auditoría (conteo de nodos).
    """
    nodes_created_count = serializers.SerializerMethodField(
        help_text="Cantidad de nodos activos creados por este usuario."
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['nodes_created_count']

    def get_nodes_created_count(self, obj):
        """Retorna el número de nodos creados que no han sido borrados lógicamente."""
        return Node.objects.filter(created_by=obj, is_deleted=False).count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer exclusivo para la creación de nuevos usuarios (POST).
    Difiere del base en que aquí los campos principales SÍ son obligatorios.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="Contraseña obligatoria (mínimo 8 caracteres)."
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirmación de la contraseña."
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 
            'role', 'first_name', 'last_name'
        ]
        # Nota: Al crear, username y email son required=True por defecto en el modelo.

    def validate(self, data):
        """Valida que las contraseñas coincidan."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        return data

    def validate_role(self, value):
        """Aplica la restricción de privilegios para la creación de SUDO."""
        request = self.context.get('request')
        if request and value == 'SUDO':
            if request.user.role != 'SUDO':
                raise serializers.ValidationError(
                    "Solo los usuarios SUDO pueden crear otros usuarios SUDO."
                )
        return value

    def create(self, validated_data):
        """Crea el usuario, hashea la contraseña y guarda."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # is_email_confirmed por defecto es False (o lo que diga el modelo)
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user