# class lead_router:

#     router_app_labels = frozenset(["lead", "invoice", "billers", "notification"])
#     default_app_labels = frozenset(
#         ["auth", "contenttypes", "admin", "sessions", "sample"]
#     )

#     def db_for_read(self, model, **hints):

#         if model._meta.app_label in self.router_app_labels:
#             return "leads_db"
#         if model._meta.app_label in self.default_app_labels:
#             return "default"
#         return None

#     def db_for_write(self, model, **hints):

#         if model._meta.app_label in self.router_app_labels:
#             return "leads_db"
#         if model._meta.app_label in self.default_app_labels:
#             return "default"
#         return None

#     def allow_relation(self, obj1, obj2, **hints):

#         # if obj1._meta.app_label in self.router_app_labels or obj2._meta.app_label in self.router_app_labels:
#         #     return True
#         # if obj1._state.db == obj2._state.db:
#         #     return True
#         if (obj1._state.db == "default" and obj2._state.db == "leads_db") or (
#             obj1._state.db == "leads_db" and obj2._state.db == "default"
#         ):
#             # Allow cross-relation for users/notifications
#             return True
#         if obj1._state.db == obj2._state.db:
#             return True
#         return None

#     def allow_migrate(self, db, app_label, model_name=None, **hints):

#         if app_label in self.router_app_labels:
#             return db == "leads_db"
#         if app_label in self.default_app_labels:
#             return db == "default"
#         return None
    



import logging

logger = logging.getLogger(__name__)

class LeadRouter:
    """
    Database router for multi-DB setup:
    - 'leads_db' : lead, invoice, billers, notifications
    - 'default'  : auth, admin, contenttypes, sessions, sample, app
    """

    # Immutable sets of app labels
    LEADS_APPS = frozenset(["lead", "invoice", "billers"])
    DEFAULT_APPS = frozenset(["auth", "contenttypes", "admin", "sessions", "teams", "sample", "app", "notification"])

    # ------------------------------
    # DB for read
    # ------------------------------
    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.LEADS_APPS:
            logger.debug(f"Routing READ for {model._meta.label} to leads_db")
            return "leads_db"
        if model._meta.app_label in self.DEFAULT_APPS:
            logger.debug(f"Routing READ for {model._meta.label} to default")
            return "default"
        return None

    # ------------------------------
    # DB for write
    # ------------------------------
    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.LEADS_APPS:
            logger.debug(f"Routing WRITE for {model._meta.label} to leads_db")
            return "leads_db"
        if model._meta.app_label in self.DEFAULT_APPS:
            logger.debug(f"Routing WRITE for {model._meta.label} to default")
            return "default"
        return None

    # ------------------------------
    # Allow relations
    # ------------------------------
    def allow_relation(self, obj1, obj2, **hints):
        db1 = obj1._state.db
        db2 = obj2._state.db

        # Allow relations within same DB
        if db1 == db2:
            return True

        # Allow cross-DB relation: Notification.user (default) ↔ Notification (leads_db)
        if (
            (db1 == "default" and db2 == "leads_db")
            or (db1 == "leads_db" and db2 == "default")
        ):
            # You can restrict further if needed
            return True

        return None

    # ------------------------------
    # Allow migrations
    # ------------------------------
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.LEADS_APPS:
            return db == "leads_db"
        if app_label in self.DEFAULT_APPS:
            return db == "default"
        return None
