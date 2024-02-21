from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)
app.secret_key = 'password' 

def get_db_connection():
    return mysql.connector.connect(
      host="localhost",
      user="root",
      password="password",
      database="food_db",
      auth_plugin='mysql_native_password'
    )

@app.route('/recipe/<int:recipe_id>')
def recipe_details(recipe_id):
  db_connection = get_db_connection()
  cursor = db_connection.cursor(dictionary=True)

  # Query for the recipe details
  cursor.execute("SELECT * FROM `recipes` WHERE `recipeId` = %s ", (recipe_id,))
  recipe = cursor.fetchone()

  # Assuming you have a table for ingredients related to the recipe
  cursor.execute("""
        SELECT i.ingredientName, i.ingredientDescription, ri.quanitiy
        FROM ingredients i
        JOIN recipe_ingredients ri ON i.ingredientId = ri.ingredientId
        WHERE ri.recipeId = %s
    """, (recipe_id,))

  ingredients = cursor.fetchall()

  for ingredient in ingredients:
    quantity = float(ingredient['quanitiy'])  # Ensure quantity is treated as a float
    # Convert to int if decimal part is 0, otherwise keep as float
    ingredient['quanitiy'] = int(quantity) if quantity.is_integer() else quantity

    
  cursor.execute("SELECT * FROM `recipe_steps` WHERE `recipeId` = %s ORDER BY `stepNumber` ASC ", (recipe_id,))
  cookSteps = cursor.fetchall()

  cursor.close()
  db_connection.close()

  # Return a template with the recipe details, or JSON data if you're using AJAX
  return render_template('recipe.html', recipe=recipe, ingredients=ingredients,cookSteps=cookSteps)

@app.route('/subscribe')
def subscribe():
    return render_template('subscribe.html')

@app.route('/subscribe', methods=['POST'])
def subscribeAction():
  email = request.form.get('email')  # Returns None if 'email' is not present

  if not email:
    # Handle the error, e.g., return an error message or redirect
    return "Email is required!", 400
  db_connection = get_db_connection()
  cursor = db_connection.cursor()
  message = ''

  try:
    cursor.execute("SELECT email FROM subscribers WHERE email = %s", (email,))
    if cursor.fetchone():
      message = 'This email already exists.'
      print("This email already exists.")

    else:
      cursor.execute("INSERT INTO subscribers (email) VALUES (%s)", (email,))
      message = 'Subscription Successful!'
      print("Subscription successful.")

  except mysql.connector.Error as err:
    print("Error: ", err)
    message = 'Database error: {e}'

  finally:
    cursor.close()
    db_connection.close()

  return render_template('message.html', message = message)

# @app.route('/all_recipes')
# def all_recipes():
#   db_connection = None
#   try: 
#     db_connection = get_db_connection()
#     cursor = db_connection.cursor(dictionary=True)

#     cursor.execute('SELECT * FROM categories')
#     categories = cursor.fetchall()

#     # Check if a category is selected
#     selected_category = request.args.get('category', '1')

#     if selected_category == '1':
#       sqlQuery = """
#         select 
#         r.recipeId,
#         r.recipeName, 
#         r.recipeDescription,
#         r.recipeImg,
#         AVG(rt.recipeRate) as avgRate, 
#         rt.ratingsNumber 
#         from recipes r
#         left join ratings rt on r.recipeId = rt.recipeId
#         group by r.recipeId, rt.ratingsNumber
#         order by r.recipeId;
#       """
#       cursor.execute(sqlQuery)
#       recipes = cursor.fetchall()
#     else:
#       cursor.execute("""
#       select 
#         r.recipeId,
#         r.recipeName, 
#         r.recipeDescription,
#         r.recipeImg,
#         AVG(rt.recipeRate) as avgRate, 
#         rt.ratingsNumber 
#         from recipes r
#         JOIN recipe_category cr ON r.recipeId = cr.recipeId and cr.categoryId = %s
#         left join ratings rt on r.recipeId = rt.recipeId
#         group by r.recipeId, rt.ratingsNumber
#         order by r.recipeId;
#       """, (selected_category,))
#       recipes = cursor.fetchall()
    
#     print(selected_category)
#     return render_template('allRecipes.html', recipes=recipes, categories= categories)
  
#   except mysql.connector.Error as err:
#     print("Error {err}")
#     return "Error occurred"
  
#   finally:
#       # Ensure the connection is closed even if an error occurs
#       if db_connection:
#           db_connection.close()
 
@app.route('/all-categories')
def all_categories():
    db_connection = None
    try: 
      db_connection = get_db_connection()
      cursor = db_connection.cursor(dictionary=True)

      cursor.execute('SELECT * FROM categories')
      categories = cursor.fetchall()
    
      return render_template('allCategories.html', categories=categories)
    except mysql.connector.Error as err:
      print("Error {err}")
      return "Error occurred"
    
    finally:
      if db_connection:
          db_connection.close()
# @app.route('/recipe/<int:recipe_id>')

@app.route('/category/<string:categoryName>')
def categoryRecipes(categoryName):
  db_connection = None
  try: 
    db_connection = get_db_connection()
    cursor = db_connection.cursor(dictionary=True)

    if categoryName == "All":
      sqlQuery = """ 
              select r.recipeId,r.recipeName, r.recipeImg, rt.ratingsNumber, avg(rt.recipeRate) as avgRate 
              from recipes r
              join ratings rt on r.recipeId = rt.recipeId
              group by r.recipeId, rt.ratingsNumber
              order by avgRate desc
          """
      cursor.execute(sqlQuery)
      categoryRecipes = cursor.fetchall()

    else:
      sqlQuery = """
        select 
          r.recipeId, 
          r.recipeName, 
          r.recipeDescription, 
          r.recipeImg,
          AVG(rt.recipeRate) AS avgRate,
          rt.ratingsNumber
        from categories c
        join recipe_category cr on c.categoryId = cr.categoryId
        join recipes r on cr.recipeId = r.recipeId
        left join ratings rt on r.recipeId = rt.recipeId
        where c.categoryName = %s
        group by r.recipeId, rt.ratingsNumber
        order by avgRate desc;
      """
      cursor.execute(sqlQuery, (categoryName,))
      categoryRecipes = cursor.fetchall()
      print(categoryRecipes)
    return render_template('recipeCategory.html', categoryRecipes = categoryRecipes)
  except mysql.connector.Error as err:
    print("Error {err}")
    return "Error occurred"
  
  finally:
    if db_connection:
        db_connection.close()

@app.route('/')
def home():
  db_connection = None
  try: 
    db_connection = get_db_connection()

    cursor = db_connection.cursor(dictionary=True)
    sqlQuery = """ 
        select r.recipeId,r.recipeName, r.recipeImg, rt.ratingsNumber, avg(rt.recipeRate) as avgRate 
        from recipes r
        join ratings rt on r.recipeId = rt.recipeId
        group by r.recipeId, rt.ratingsNumber
        order by avgRate desc
        limit 4;
    """
    cursor.execute(sqlQuery)
    popular_recipes = cursor.fetchall()
    return render_template('index.html', popular_recipes=popular_recipes)
  
  except mysql.connector.Error as err:
    print("Error {err}")
    return "Error occurred"
  
  finally:
      # Ensure the connection is closed even if an error occurs
      if db_connection:
          db_connection.close()


if __name__ == '__main__':
    app.run(debug=True)

    