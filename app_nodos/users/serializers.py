# app_nodos/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# Importación condicional para evitar error circular
try:
    from nodes.models import Node  # Importación necesaria para auditoría
except ImportError:
    Node = None


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer base para operaciones de lectura (GET) y actualización (PUT/PATCH).
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        min_length=8,
        help_text="Dejar en blanco para mantener la contraseña actual. Mínimo 8 caracteres."
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_email_confirmed', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'password', 'is_deleted'  # Añadido is_deleted
        ]
        read_only_fields = [
            'date_joined', 'last_login', 'is_staff', 'is_superuser', 'is_deleted'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False},
            'is_active': {'required': False},
            'is_email_confirmed': {'required': False},
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
        if not value:
            raise serializers.ValidationError("El email no puede estar vacío.")
            
        value = value.lower().strip()
        
        query = User.objects.filter(email__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        
        return value

    def validate_password(self, value):
        """
        Valida la fortaleza de la contraseña si se proporciona.
        """
        if value:
            try:
                password_validation.validate_password(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """
        Validaciones adicionales a nivel de objeto.
        """
        # CORRECCIÓN: Verificar que no se intente activar un usuario eliminado
        if self.instance and self.instance.is_deleted:
            if data.get('is_active', False):
                raise serializers.ValidationError({
                    'is_active': 'No se puede activar un usuario eliminado.'
                })
        
        # CORRECCIÓN: USER no puede cambiar su propio rol
        request = self.context.get('request')
        if request and self.instance and request.user.pk == self.instance.pk:
            if 'role' in data and data['role'] != self.instance.role:
                raise serializers.ValidationError({
                    'role': 'No puedes cambiar tu propio rol.'
                })
        
        return data

    def update(self, instance, validated_data):
        """
        Actualiza la instancia del usuario.
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
    Serializer extendido para la vista de detalle.
    """
    nodes_created_count = serializers.SerializerMethodField(
        help_text="Cantidad de nodos activos creados por este usuario."
    )
    
    role_display = serializers.SerializerMethodField(
        help_text="Nombre completo del rol."
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['nodes_created_count', 'role_display']

    def get_nodes_created_count(self, obj):
        """
        Retorna el número de nodos creados que no han sido borrados lógicamente.
        """
        if Node is None:
            return 0
            
        try:
            # CORRECCIÓN: Usar la relación inversa si existe
            if hasattr(obj, 'nodes_created'):
                return obj.nodes_created.filter(is_deleted=False).count()
            else:
                return Node.objects.filter(created_by=obj, is_deleted=False).count()
        except Exception:
            return 0

    def get_role_display(self, obj):
        """
        Retorna el nombre completo del rol.
        """
        return obj.get_role_display_name() if hasattr(obj, 'get_role_display_name') else obj.get_role_display()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer exclusivo para la creación de nuevos usuarios (POST).
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
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_username(self, value):
        """
        Valida que el username sea único.
        """
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está registrado.")
        return value

    def validate_email(self, value):
        """
        Valida el email al crear un usuario.
        """
        if not value:
            raise serializers.ValidationError("El email es obligatorio.")
            
        value = value.lower().strip()
        
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        
        return value

    def validate_password(self, value):
        """
        Valida la fortaleza de la contraseña.
        """
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """
        Valida que las contraseñas coincidan.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        return data

    def validate_role(self, value):
        """
        Aplica la restricción de privilegios para la creación de SUDO.
        """
        request = self.context.get('request')
        if request and value == 'SUDO':
            if request.user.role != 'SUDO':
                raise serializers.ValidationError(
                    "Solo los usuarios SUDO pueden crear otros usuarios SUDO."
                )
        return value

    def create(self, validated_data):
        """
        Crea el usuario, hashea la contraseña y guarda.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # CORRECCIÓN: Por defecto is_email_confirmed=False para mayor seguridad
        validated_data.setdefault('is_email_confirmed', False)
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user