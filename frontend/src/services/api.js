import axios from 'axios';

const api = axios.create({
    // Usa la variable de entorno VITE_API_URL (para Render) o localhost (para desarrollo)
    baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000', 
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getPantryItems = () => api.get('/pantry/');
export const addPantryItem = (data) => api.post('/pantry/', data);
export const updatePantryItem = (id, data) => api.patch(`/pantry/${id}`, data);
export const deletePantryItem = (id) => api.delete(`/pantry/${id}`);
export const searchIngredients = (query) => api.get('/ingredients/search', { params: query });

// Shopping List
export const getShoppingList = (params) => api.get('/shopping-list/', { params });
export const addShoppingListItem = (data) => api.post('/shopping-list/', data);
export const updateShoppingListItem = (id, data) => api.patch(`/shopping-list/${id}`, data);
export const deleteShoppingListItem = (id) => api.delete(`/shopping-list/${id}`);

// Recipes
export const getRecipes = (params) => api.get('/recipes/', { params });
export const getRecipeById = (id) => api.get(`/recipes/${id}`);
export const addMissingToShoppingList = (recipeId, data) => api.post(`/recipes/${recipeId}/shopping-list/add-missing`, data);
export const addIngredientToShoppingList = (recipeId, ingredientId) => api.post(`/recipes/${recipeId}/shopping-list/add-ingredient`, { ingredient_id: ingredientId });
export const getExpiringRecommendations = (params) => api.get('/recipes/recommendations/expiring', { params });

// Food Log
export const logRecipe = (data) => api.post('/log/recipe', data);
export const logIngredient = (data) => api.post('/log/ingredient', data);
export const getDailySummary = (date) => api.get('/log/daily-summary', { params: { log_date: date } });
export const deleteLogEntry = (id) => api.delete(`/log/${id}`);

// Profile
export const getProfile = () => api.get('/profile/');
export const updateProfile = (data) => api.patch('/profile/', data);

export default api;

