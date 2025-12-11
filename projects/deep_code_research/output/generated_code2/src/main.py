if response is None:
                # FIX: Explicitly log when the client returns None for a valid query,
                # as this was the observed failure mode for the first input.
                logger.error(f"Client returned None for query: '{query}'. Check DRClient implementation or configuration.")
                return None