from flask import Flask, render_template, request
import mysql.connector

# Initialize Flask app
app = Flask(__name__)
# Secret key for session management to maintain session state
app.secret_key = 'password' 

# Establish database connection
def get_db_connection():
    return mysql.connector.connect(
      host="localhost",
      user="root",
      password="password",
      database="food_db",
      auth_plugin='mysql_native_password'
    )

# Route for displaying details of a specific recipe by recipe id id
@app.route('/recipe/<int:recipe_id>')
def recipe_details(recipe_id):
  # Establish database connection
  db_connection = get_db_connection()
  cursor = db_connection.cursor(dictionary=True)
  
  # Retrieve the specific recipe by its ID
  cursor.execute("SELECT * FROM `recipes` WHERE `recipeId` = %s ", (recipe_id,))
  recipe = cursor.fetchone()
  
  # Retrieve ingredients for the specific recipe
  cursor.execute("""
        SELECT i.ingredientName, i.ingredientDescription, ri.quanitiy
        FROM ingredients i
        JOIN recipe_ingredients ri ON i.ingredientId = ri.ingredientId
        WHERE ri.recipeId = %s
    """, (recipe_id,))

  ingredients = cursor.fetchall()
  # Convert quantity to integer if it's a whole number, else keep as float
  for ingredient in ingredients:
    quantity = float(ingredient['quanitiy'])  
    ingredient['quanitiy'] = int(quantity) if quantity.is_integer() else quantity
  
  # Retrieve cooking steps for the recipe, ordered by step number
  cursor.execute("SELECT * FROM `recipe_steps` WHERE `recipeId` = %s ORDER BY `stepNumber` ASC ", (recipe_id,))
  cookSteps = cursor.fetchall()

  # Close cursor and database connection
  cursor.close()
  db_connection.close()

  # Render template with recipe details
  return render_template('recipe.html', recipe=recipe, ingredients=ingredients,cookSteps=cookSteps)

# Route for subscription page
@app.route('/subscribe')
def subscribe():
    return render_template('subscribe.html')

# Route to handle subscription action
@app.route('/subscribe', methods=['POST'])
def subscribeAction():
  # Retrieve email from form
  email = request.form.get('email') 

  # Retrieve email from form
  if not email:
    # Handle error for missing email
    return "Email is required!", 400

  # Establish database connection
  db_connection = get_db_connection()
  cursor = db_connection.cursor()
  message = ''

  try:
    # Check if email already exists in subscribers
    cursor.execute("SELECT email FROM subscribers WHERE email = %s", (email,))
    if cursor.fetchone():
      message = 'This email already exists.'
      print("This email already exists.")
    
    # Insert new subscriber
    else:
      cursor.execute("INSERT INTO subscribers (email) VALUES (%s)", (email,))
      message = 'Subscription Successful!'
      print("Subscription successful.")

  except mysql.connector.Error as err:
    # Handle database error
    print("Error: ", err)
    message = 'Database error: {e}'

  finally:
    # Close cursor and database connection
    cursor.close()
    db_connection.close()

  # Render message template with subscription status
  return render_template('message.html', message = message)

# Route for displaying all categories
@app.route('/all-categories')
def all_categories():
    db_connection = None
    try: 
      # Establish database connection
      db_connection = get_db_connection()
      cursor = db_connection.cursor(dictionary=True)

      # Retrieve all categories
      cursor.execute('SELECT * FROM categories')
      categories = cursor.fetchall()
    
      # Render template with all categories
      return render_template('allCategories.html', categories=categories)
    except mysql.connector.Error as err:
      # Handle database error
      print("Error {err}")
      return "Error occurred"
    
    finally:
      # Close database connection
      if db_connection:
          db_connection.close()

# Route for displaying recipes by category
@app.route('/category/<string:categoryName>')
def categoryRecipes(categoryName):
  db_connection = None
  try: 
    # Establish database connection
    db_connection = get_db_connection()
    cursor = db_connection.cursor(dictionary=True)
    
    # Get data based on category name
    if categoryName == "All":
      # Retrieve all recipes if category is "All"
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
      # Retrieve recipes specific to a category
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

    # Render template with recipes of a specific category
    return render_template('recipeCategory.html', categoryRecipes = categoryRecipes)
  except mysql.connector.Error as err:
    # Handle database error
    print("Error {err}")
    return "Error occurred"
  
  finally:
    # Close database connection
    if db_connection:
        db_connection.close()

# Home route displaying popular recipes
@app.route('/')
def home():
  db_connection = None
  try: 
    # Establish database connection
    db_connection = get_db_connection()

    cursor = db_connection.cursor(dictionary=True)
    # Retrieve top 4 popular recipes based on average rating
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

    # Render home template with popular recipes
    return render_template('index.html', popular_recipes=popular_recipes)
  
  except mysql.connector.Error as err:
    # Handle database error
    print("Error {err}")
    return "Error occurred"
  
  finally:
      # Close database connection
      if db_connection:
          db_connection.close()

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

    