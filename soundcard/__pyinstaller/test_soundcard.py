def test_pyi_soundcard(pyi_builder):
    pyi_builder.test_source(
        """
        import soundcard
    """
    )
