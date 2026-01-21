import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SpoonacularClient:
    BASE_URL = "https://api.spoonacular.com"

    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, params={"apiKey": self.api_key})

    async def close(self):
        await self.client.aclose()

    async def _get(self, endpoint: str, params: dict = None) -> dict:
        try:
            response = await self.client.get(endpoint, params=params)
            
            # Log quota if present
            if "X-API-Quota-Used" in response.headers:
                quota_used = response.headers["X-API-Quota-Used"]
                logger.info(f"Spoonacular Quota Used: {quota_used}")

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Spoonacular API Error: {e.response.status_code} - {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"Spoonacular Connection Error: {str(e)}")
            raise e

    async def search_recipes(
        self,
        query: str | None = None,
        diet: str | None = None,
        intolerances: list[str] | None = None,
        offset: int = 0,
        number: int = 10,
    ) -> dict:
        """
        Wraps GET /recipes/complexSearch with:
        - addRecipeInformation=true
        - addRecipeNutrition=true
        """
        params = {
            "addRecipeInformation": "true",
            "addRecipeNutrition": "true",
            "offset": offset,
            "number": number,
        }
        if query:
            params["query"] = query
        if diet:
            params["diet"] = diet
        if intolerances:
            params["intolerances"] = ",".join(intolerances)

        return await self._get("/recipes/complexSearch", params=params)

    async def get_recipe_information(self, recipe_id: int) -> dict:
        """
        Wraps GET /recipes/{id}/information?includeNutrition=true.
        """
        params = {"includeNutrition": "true"}
        return await self._get(f"/recipes/{recipe_id}/information", params=params)

    async def get_ingredient_information(self, ingredient_id: int, amount: float = 100.0, unit: str = "g") -> dict:
        """
        Wraps GET /food/ingredients/{id}/information?amount=...&unit=...
        Returns ingredient nutrition for that amount.
        """
        params = {
            "amount": amount,
            "unit": unit
        }
        return await self._get(f"/food/ingredients/{ingredient_id}/information", params=params)

spoonacular_client = SpoonacularClient()
