from df_model_actions.models import ModelAction


def signal_loader() -> None:
    for model_action in ModelAction.objects.all():
        model_action.register_model_signal()
