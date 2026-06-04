#!/usr/bin/env python3

def main():
    import simple_data_catalog_generator.analysis_functions as af
    import simple_data_catalog_generator.create_data_catalog as cdc

    original = af.create_theme_word_cloud

    def safe_create_theme_word_cloud(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except ValueError as e:
            msg = str(e)
            if "We need at least 1 word to plot a word cloud" in msg and "got 0" in msg:
                return None
            raise

    af.create_theme_word_cloud = safe_create_theme_word_cloud
    cdc.create_data_catalog()


if __name__ == "__main__":
    main()
