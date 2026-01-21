import React, { useEffect, useState } from 'react';
import { getRecipeById, addMissingToShoppingList, addIngredientToShoppingList, logRecipe } from '../services/api';
import { Loader, ArrowLeft, Users, Flame, Beef, Wheat, Droplets, UtensilsCrossed, Check, AlertCircle, ShoppingCart, Plus, Calendar } from 'lucide-react';

export default function RecipeDetailView({ recipeId, onBack }) {
    const [recipe, setRecipe] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [addingAll, setAddingAll] = useState(false);
    const [addingIngredient, setAddingIngredient] = useState(null);
    const [toast, setToast] = useState(null);

    const fetchRecipe = async () => {
        try {
            setError(null);
            const res = await getRecipeById(recipeId);
            setRecipe(res.data);
        } catch (err) {
            console.error("Error fetching recipe:", err);
            if (err.response?.status === 404) {
                setError("Receta no encontrada.");
            } else {
                setError("No se pudo cargar la receta. Verifica la conexión.");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (recipeId) {
            setLoading(true);
            fetchRecipe();
        }
    }, [recipeId]);

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleAddAllMissing = async () => {
        setAddingAll(true);
        try {
            const res = await addMissingToShoppingList(recipeId, { include_partially_available: true });
            const count = res.data.length;
            if (count > 0) {
                showToast(`${count} ingrediente(s) añadido(s) a la lista`);
            } else {
                showToast('No hay ingredientes faltantes', 'info');
            }
        } catch (err) {
            console.error("Error adding missing ingredients:", err);
            showToast('Error al añadir ingredientes', 'error');
        } finally {
            setAddingAll(false);
        }
    };

    const handleAddSingleIngredient = async (ingredientId) => {
        setAddingIngredient(ingredientId);
        try {
            await addIngredientToShoppingList(recipeId, ingredientId);
            showToast('Ingrediente añadido a la lista');
        } catch (err) {
            console.error("Error adding ingredient:", err);
            showToast('Error al añadir ingrediente', 'error');
        } finally {
            setAddingIngredient(null);
        }
    };

    const handleLogRecipe = async () => {
        const servingsStr = prompt("¿Cuántas raciones has comido?", "1.0");
        if (!servingsStr) return;

        const servings = parseFloat(servingsStr);
        if (isNaN(servings) || servings <= 0) {
            alert("Por favor introduce un número válido.");
            return;
        }

        try {
            await logRecipe({ recipe_id: recipe.id, servings: servings });
            showToast('Receta registrada en el diario');
        } catch (error) {
            console.error("Error logging recipe:", error);
            showToast('Error al registrar en el diario', 'error');
        }
    };

    // Helper to get nutrition values
    const getNutrition = (nutrition, key) => {
        if (!nutrition) return null;
        return nutrition[key] || null;
    };

    // Count missing ingredients
    const getMissingCount = () => {
        if (!recipe?.ingredients) return 0;
        return recipe.ingredients.filter(ing => !ing.is_available).length;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <Loader className="animate-spin text-slate-400" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
                <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10">
                    <div className="max-w-3xl mx-auto px-4 h-16 flex items-center">
                        <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg mr-2">
                            <ArrowLeft size={20} />
                        </button>
                        <h1 className="font-bold text-xl">Error</h1>
                    </div>
                </nav>
                <main className="max-w-3xl mx-auto px-4 py-8">
                    <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-red-200">
                        <div className="bg-red-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            <UtensilsCrossed className="text-red-300" size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-red-700">{error}</h3>
                        <button
                            onClick={onBack}
                            className="mt-4 text-rose-600 font-medium hover:underline"
                        >
                            Volver a recetas
                        </button>
                    </div>
                </main>
            </div>
        );
    }

    const nutrition = recipe.nutrition_totals_per_serving;
    const missingCount = getMissingCount();

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Toast Notification */}
            {toast && (
                <div className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 ${toast.type === 'success' ? 'bg-emerald-500 text-white' :
                    toast.type === 'error' ? 'bg-red-500 text-white' :
                        'bg-slate-600 text-white'
                    }`}>
                    <ShoppingCart size={18} />
                    <span className="font-medium">{toast.message}</span>
                </div>
            )}

            {/* Header */}
            <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10">
                <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center">
                        <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg mr-2">
                            <ArrowLeft size={20} />
                        </button>
                        <h1 className="font-bold text-xl truncate max-w-[200px] sm:max-w-md">{recipe.title}</h1>
                    </div>
                    <button
                        onClick={handleLogRecipe}
                        className="bg-indigo-50 text-indigo-600 hover:bg-indigo-100 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1 transition-colors"
                    >
                        <Calendar size={16} />
                        <span className="hidden sm:inline">Añadir al Diario</span>
                    </button>
                </div>
            </nav>

            <main className="max-w-3xl mx-auto">
                {/* Hero Image */}
                {recipe.image_url ? (
                    <div className="h-64 overflow-hidden">
                        <img
                            src={recipe.image_url}
                            alt={recipe.title}
                            className="w-full h-full object-cover"
                        />
                    </div>
                ) : (
                    <div className="h-64 bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center">
                        <UtensilsCrossed className="text-rose-300" size={64} />
                    </div>
                )}

                <div className="px-4 py-6 space-y-6">
                    {/* Title & Servings */}
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800 mb-2">{recipe.title}</h2>
                        {recipe.servings && (
                            <span className="inline-flex items-center gap-1 text-slate-500 bg-slate-100 px-3 py-1 rounded-full text-sm">
                                <Users size={14} />
                                {recipe.servings} raciones
                            </span>
                        )}
                    </div>

                    {/* Intolerance Warnings */}
                    {recipe.intolerance_warnings && recipe.intolerance_warnings.length > 0 && (
                        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
                            <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                            <div>
                                <h4 className="font-semibold text-red-700 mb-1">⚠️ Contiene alérgenos</h4>
                                <p className="text-sm text-red-600">
                                    Esta receta contiene: <strong>{recipe.intolerance_warnings.join(', ')}</strong>
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Diet badges */}
                    {recipe.diets && recipe.diets.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {recipe.diets.map((diet, idx) => (
                                <span key={idx} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full capitalize">
                                    {diet}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Summary */}
                    {recipe.summary && (
                        <div className="bg-white rounded-xl p-4 border border-slate-100">
                            <p className="text-slate-600 text-sm leading-relaxed">{recipe.summary}</p>
                        </div>
                    )}

                    {/* Nutrition Card */}
                    {nutrition && (
                        <div className="bg-white rounded-xl p-4 border border-slate-100">
                            <h3 className="font-semibold text-slate-700 mb-3">Nutrición por ración</h3>
                            <div className="grid grid-cols-4 gap-3 text-center">
                                {getNutrition(nutrition, 'calories') && (
                                    <div className="bg-orange-50 rounded-lg p-3">
                                        <Flame className="mx-auto text-orange-500 mb-1" size={18} />
                                        <p className="text-lg font-bold text-slate-800">{Math.round(getNutrition(nutrition, 'calories'))}</p>
                                        <p className="text-xs text-slate-500">kcal</p>
                                    </div>
                                )}
                                {getNutrition(nutrition, 'protein') && (
                                    <div className="bg-emerald-50 rounded-lg p-3">
                                        <Beef className="mx-auto text-emerald-500 mb-1" size={18} />
                                        <p className="text-lg font-bold text-slate-800">{Math.round(getNutrition(nutrition, 'protein'))}g</p>
                                        <p className="text-xs text-slate-500">proteína</p>
                                    </div>
                                )}
                                {getNutrition(nutrition, 'carbohydrates') && (
                                    <div className="bg-amber-50 rounded-lg p-3">
                                        <Wheat className="mx-auto text-amber-500 mb-1" size={18} />
                                        <p className="text-lg font-bold text-slate-800">{Math.round(getNutrition(nutrition, 'carbohydrates'))}g</p>
                                        <p className="text-xs text-slate-500">carbos</p>
                                    </div>
                                )}
                                {getNutrition(nutrition, 'fat') && (
                                    <div className="bg-purple-50 rounded-lg p-3">
                                        <Droplets className="mx-auto text-purple-500 mb-1" size={18} />
                                        <p className="text-lg font-bold text-slate-800">{Math.round(getNutrition(nutrition, 'fat'))}g</p>
                                        <p className="text-xs text-slate-500">grasa</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Ingredients */}
                    {recipe.ingredients && recipe.ingredients.length > 0 && (
                        <div className="bg-white rounded-xl p-4 border border-slate-100">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-slate-700">Ingredientes</h3>
                                {missingCount > 0 && (
                                    <button
                                        onClick={handleAddAllMissing}
                                        disabled={addingAll}
                                        className="text-sm bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors"
                                    >
                                        <ShoppingCart size={14} />
                                        {addingAll ? 'Añadiendo...' : `Añadir ${missingCount} faltante(s)`}
                                    </button>
                                )}
                            </div>
                            <ul className="space-y-2">
                                {recipe.ingredients.map((ing, idx) => (
                                    <li
                                        key={idx}
                                        className={`flex items-center justify-between py-3 px-3 rounded-lg border ${ing.is_available
                                            ? 'border-emerald-200 bg-emerald-50/50'
                                            : 'border-orange-200 bg-orange-50/50'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            {/* Availability icon */}
                                            {ing.is_available ? (
                                                <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
                                                    <Check size={14} className="text-white" />
                                                </div>
                                            ) : (
                                                <div className="w-6 h-6 rounded-full bg-orange-400 flex items-center justify-center">
                                                    <AlertCircle size={14} className="text-white" />
                                                </div>
                                            )}
                                            <div>
                                                <span className="text-slate-800 capitalize font-medium">{ing.name}</span>
                                                <div className="text-sm text-slate-500">
                                                    {ing.amount} {ing.unit}
                                                    {ing.is_available ? (
                                                        <span className="ml-2 text-emerald-600">✓ Disponible</span>
                                                    ) : ing.pantry_quantity ? (
                                                        <span className="ml-2 text-orange-600">
                                                            (tienes {ing.pantry_quantity} {ing.pantry_unit}, falta {ing.missing_quantity})
                                                        </span>
                                                    ) : (
                                                        <span className="ml-2 text-orange-600">
                                                            (te falta {ing.missing_quantity || ing.amount} {ing.unit})
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Add to list button */}
                                        {!ing.is_available && (
                                            <button
                                                onClick={() => handleAddSingleIngredient(ing.id)}
                                                disabled={addingIngredient === ing.id}
                                                className="p-2 text-emerald-600 hover:bg-emerald-100 rounded-lg transition-colors disabled:opacity-50"
                                                title="Añadir a la lista"
                                            >
                                                {addingIngredient === ing.id ? (
                                                    <Loader size={18} className="animate-spin" />
                                                ) : (
                                                    <Plus size={18} />
                                                )}
                                            </button>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Instructions */}
                    {recipe.instructions && (
                        <div className="bg-white rounded-xl p-4 border border-slate-100">
                            <h3 className="font-semibold text-slate-700 mb-3">Instrucciones</h3>
                            <div
                                className="text-slate-600 text-sm leading-relaxed prose prose-sm max-w-none"
                                dangerouslySetInnerHTML={{ __html: recipe.instructions }}
                            />
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
