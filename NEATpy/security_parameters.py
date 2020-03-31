

class SecurityParameters:
    def __init__(self):
        pass

    def add_identity(self, identity):
        return NotImplementedError

    def add_private_key(self, private_key, public_key):
        return NotImplementedError

    def add_pre_shared_key(self, key, identity):
        return NotImplementedError

    def add_supported_group(self, group):
        return NotImplementedError

    def add_cipher_suite(self, cipher_suite):
        return NotImplementedError

    def add_signature_algorithm(self, signature_algorithm):
        return NotImplementedError

    def set_session_cache_capacity(self, capacity):
        return NotImplementedError

    def set_session_cache_lifetime(self, lifetime):
        return NotImplementedError

    def set_session_cacahe_policy(self, policy):
        return NotImplementedError

    def set_trust_verification_callback(self, callback):
        return NotImplementedError

    def set_identity_challenge_callback(self, callback):
        return NotImplementedError
