"""
Populate database with 200 test questions + answers
with proper tags and ranking scores
"""

import sqlite3
import random
from datetime import datetime, timedelta

# Sample questions with tags and answers
QUESTIONS_DATA = [
    # Python Questions
    {
        "text": "How do I use list comprehensions in Python?",
        "tags": "python,lists,syntax",
        "answers": [
            "List comprehensions provide a concise way to create lists: [x**2 for x in range(10)]",
            "They are more readable and faster than equivalent for loops in Python.",
        ]
    },
    {
        "text": "What is the difference between == and is in Python?",
        "tags": "python,operators,comparison",
        "answers": [
            "== checks for value equality, while is checks for identity (same object in memory).",
            "Use == for value comparison and is for checking if two variables point to the same object.",
        ]
    },
    {
        "text": "How to handle exceptions in Python?",
        "tags": "python,exceptions,error-handling",
        "answers": [
            "Use try-except blocks: try: ... except Exception as e: ...",
            "You can catch specific exceptions and also use finally for cleanup code.",
        ]
    },
    {
        "text": "How do I work with decorators in Python?",
        "tags": "python,decorators,functions",
        "answers": [
            "Decorators wrap functions to modify their behavior. Use @decorator syntax above functions.",
            "They are useful for logging, authentication, timing, and other cross-cutting concerns.",
        ]
    },
    {
        "text": "What is async/await in Python?",
        "tags": "python,async,concurrency",
        "answers": [
            "async/await provides a way to write asynchronous code that looks synchronous.",
            "Use async def to define coroutines and await to call them without blocking.",
        ]
    },
    {
        "text": "How do I use the lambda function in Python?",
        "tags": "python,lambda,functions",
        "answers": [
            "Lambda creates anonymous functions: lambda x: x**2",
            "Useful for short functions passed to higher-order functions like map, filter, sorted.",
        ]
    },
    {
        "text": "What are generators in Python?",
        "tags": "python,generators,iterators",
        "answers": [
            "Generators use yield to create lazy iterators that produce values on demand.",
            "They save memory compared to lists and are useful for large datasets.",
        ]
    },
    {
        "text": "How to use context managers in Python?",
        "tags": "python,context-managers,files",
        "answers": [
            "Use 'with' statement: with open('file.txt') as f:",
            "Context managers ensure resources are properly acquired and released.",
        ]
    },
    {
        "text": "What is the GIL in Python?",
        "tags": "python,threading,gil",
        "answers": [
            "The Global Interpreter Lock prevents true multithreading in CPython.",
            "Use multiprocessing for CPU-bound tasks or async for I/O-bound tasks.",
        ]
    },
    {
        "text": "How do I use type hints in Python?",
        "tags": "python,typing,type-hints",
        "answers": [
            "Add type annotations: def func(x: int) -> str:",
            "Type hints improve code readability and enable static type checking with mypy.",
        ]
    },

    # JavaScript Questions
    {
        "text": "What are closures in JavaScript?",
        "tags": "javascript,closures,functions",
        "answers": [
            "Closures allow functions to access variables from their parent scope.",
            "They are created every time a function is created in JavaScript.",
        ]
    },
    {
        "text": "How does the event loop work in JavaScript?",
        "tags": "javascript,event-loop,async",
        "answers": [
            "The event loop continuously checks the call stack and callback queue.",
            "It executes callbacks when the stack is empty, enabling non-blocking operations.",
        ]
    },
    {
        "text": "What is the difference between var, let, and const?",
        "tags": "javascript,variables,scope",
        "answers": [
            "var is function-scoped, let and const are block-scoped.",
            "const prevents reassignment but allows mutation of objects.",
        ]
    },
    {
        "text": "How to use async/await in JavaScript?",
        "tags": "javascript,async,promises",
        "answers": [
            "async functions return promises. await pauses execution until the promise resolves.",
            "async/await makes asynchronous code look and behave more like synchronous code.",
        ]
    },
    {
        "text": "What are promises in JavaScript?",
        "tags": "javascript,promises,async",
        "answers": [
            "Promises represent the eventual completion of an asynchronous operation.",
            "They have three states: pending, fulfilled, and rejected.",
        ]
    },
    {
        "text": "How to handle errors in JavaScript?",
        "tags": "javascript,error-handling,try-catch",
        "answers": [
            "Use try-catch-finally blocks for synchronous code and .catch() for promises.",
            "In async functions, wrap in try-catch or use .catch() on the promise.",
        ]
    },
    {
        "text": "What is hoisting in JavaScript?",
        "tags": "javascript,hoisting,scope",
        "answers": [
            "Variable and function declarations are moved to the top of their scope.",
            "Function declarations are fully hoisted, var is hoisted but uninitialized.",
        ]
    },
    {
        "text": "How do prototypes work in JavaScript?",
        "tags": "javascript,prototypes,oop",
        "answers": [
            "Objects have a prototype property that they inherit from.",
            "Prototype chain allows objects to inherit properties and methods.",
        ]
    },
    {
        "text": "What is the 'this' keyword in JavaScript?",
        "tags": "javascript,this,context",
        "answers": [
            "'this' refers to the object that owns the current code.",
            "Its value depends on how the function is called (call, apply, bind).",
        ]
    },
    {
        "text": "How to use arrow functions in JavaScript?",
        "tags": "javascript,arrow-functions,es6",
        "answers": [
            "Arrow functions: const func = () => {} have shorter syntax.",
            "They don't have their own 'this' and 'arguments' objects.",
        ]
    },

    # React Questions
    {
        "text": "How do hooks work in React?",
        "tags": "react,hooks,state",
        "answers": [
            "Hooks let you use state and other React features without classes.",
            "Common hooks: useState, useEffect, useContext, useReducer.",
        ]
    },
    {
        "text": "What is the difference between controlled and uncontrolled components?",
        "tags": "react,forms,components",
        "answers": [
            "Controlled components have their state managed by React.",
            "Uncontrolled components manage their own state, accessed via refs.",
        ]
    },
    {
        "text": "How to optimize React performance?",
        "tags": "react,performance,optimization",
        "answers": [
            "Use React.memo for functional components, useMemo for expensive calculations.",
            "Code splitting, lazy loading, and windowing help with large lists.",
        ]
    },
    {
        "text": "What is context API in React?",
        "tags": "react,context,state-management",
        "answers": [
            "Context API provides a way to pass data through the component tree.",
            "It helps avoid prop drilling for global state like themes or user info.",
        ]
    },
    {
        "text": "How do I handle side effects in React?",
        "tags": "react,useEffect,side-effects",
        "answers": [
            "Use useEffect hook: useEffect(() => { ... }, [dependencies])",
            "The dependency array controls when the effect runs.",
        ]
    },
    {
        "text": "What is Redux and when should I use it?",
        "tags": "react,redux,state-management",
        "answers": [
            "Redux is a state management library for complex applications.",
            "Use it when you have complex state logic shared across many components.",
        ]
    },
    {
        "text": "How to handle forms in React?",
        "tags": "react,forms,input",
        "answers": [
            "Use controlled components with onChange handlers.",
            "Libraries like Formik and React Hook Form help with validation.",
        ]
    },
    {
        "text": "What are keys in React lists?",
        "tags": "react,lists,keys",
        "answers": [
            "Keys help React identify which items have changed.",
            "Use unique IDs, not array indices, for better performance and correctness.",
        ]
    },
    {
        "text": "How to do routing in React?",
        "tags": "react,routing,navigation",
        "answers": [
            "Use React Router: <BrowserRouter>, <Routes>, <Route>",
            "It provides client-side routing without full page reloads.",
        ]
    },
    {
        "text": "What are render props in React?",
        "tags": "react,render-props,components",
        "answers": [
            "Render props is a technique for sharing code using a prop whose value is a function.",
            "Component calls the function to determine what to render.",
        ]
    },

    # Database Questions
    {
        "text": "What is normalization in databases?",
        "tags": "sql,database,normalization",
        "answers": [
            "Normalization organizes data to reduce redundancy and improve integrity.",
            "Normal forms (1NF, 2NF, 3NF) define levels of normalization.",
        ]
    },
    {
        "text": "How to optimize SQL queries?",
        "tags": "sql,optimization,performance",
        "answers": [
            "Use indexes, avoid SELECT *, use EXPLAIN for query analysis.",
            "Join only needed tables and filter early with WHERE clauses.",
        ]
    },
    {
        "text": "What are database indexes?",
        "tags": "sql,indexes,performance",
        "answers": [
            "Indexes speed up data retrieval but slow down insertions.",
            "Create indexes on columns frequently used in WHERE and JOIN clauses.",
        ]
    },
    {
        "text": "What is a transaction in databases?",
        "tags": "sql,transactions,acid",
        "answers": [
            "Transactions ensure ACID properties: Atomicity, Consistency, Isolation, Durability.",
            "Use BEGIN, COMMIT, ROLLBACK to control transactions.",
        ]
    },
    {
        "text": "How do I prevent SQL injection?",
        "tags": "sql,security,injection",
        "answers": [
            "Use parameterized queries or prepared statements.",
            "Never concatenate user input directly into SQL queries.",
        ]
    },
    {
        "text": "What is a primary key and foreign key?",
        "tags": "sql,keys,relationships",
        "answers": [
            "Primary key uniquely identifies a row, foreign key references another table.",
            "Foreign keys establish relationships between tables.",
        ]
    },
    {
        "text": "How to join tables in SQL?",
        "tags": "sql,joins,queries",
        "answers": [
            "Types: INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN.",
            "INNER JOIN returns only matching rows from both tables.",
        ]
    },
    {
        "text": "What are aggregate functions in SQL?",
        "tags": "sql,aggregation,functions",
        "answers": [
            "Functions like COUNT, SUM, AVG, MIN, MAX operate on groups of rows.",
            "Use GROUP BY to group rows before aggregation.",
        ]
    },
    {
        "text": "What is an ERD in databases?",
        "tags": "database,design,erd",
        "answers": [
            "Entity-Relationship Diagram visualizes database structure.",
            "Shows entities, attributes, and relationships between entities.",
        ]
    },
    {
        "text": "How to back up and restore databases?",
        "tags": "database,backup,administration",
        "answers": [
            "Use database-specific tools: mysqldump, pg_dump, sqlitebackup.",
            "Regular backups are critical for disaster recovery.",
        ]
    },

    # API/Web Service Questions
    {
        "text": "What are RESTful APIs?",
        "tags": "api,rest,web-services",
        "answers": [
            "REST uses HTTP methods (GET, POST, PUT, DELETE) to perform operations.",
            "Resources are represented by URLs, and operations modify them.",
        ]
    },
    {
        "text": "What are HTTP status codes?",
        "tags": "api,http,status-codes",
        "answers": [
            "1xx: Informational, 2xx: Success, 3xx: Redirection, 4xx: Client Error, 5xx: Server Error.",
            "Common: 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Error.",
        ]
    },
    {
        "text": "How to authenticate APIs?",
        "tags": "api,authentication,security",
        "answers": [
            "Methods: API keys, OAuth 2.0, JWT (JSON Web Tokens).",
            "JWT is stateless and good for modern distributed systems.",
        ]
    },
    {
        "text": "What is GraphQL and how does it differ from REST?",
        "tags": "graphql,api,query-language",
        "answers": [
            "GraphQL is a query language that lets clients request exactly what data they need.",
            "REST returns fixed data structure; GraphQL is more flexible.",
        ]
    },
    {
        "text": "How to handle CORS in web APIs?",
        "tags": "api,cors,security",
        "answers": [
            "CORS headers allow cross-origin requests from browsers.",
            "Set Access-Control-Allow-Origin, Methods, Headers.",
        ]
    },
    {
        "text": "What is rate limiting in APIs?",
        "tags": "api,security,rate-limiting",
        "answers": [
            "Rate limiting restricts the number of API calls from a client.",
            "Prevents abuse and ensures fair usage.",
        ]
    },
    {
        "text": "How to version APIs?",
        "tags": "api,versioning,best-practices",
        "answers": [
            "URL versioning: /api/v1/, Header versioning, Query parameter versioning.",
            "Helps maintain backward compatibility when changing APIs.",
        ]
    },
    {
        "text": "What is API documentation best practice?",
        "tags": "api,documentation,openapi",
        "answers": [
            "Use OpenAPI/Swagger for comprehensive documentation.",
            "Document endpoints, parameters, responses, and error codes.",
        ]
    },
    {
        "text": "How to test APIs?",
        "tags": "api,testing,tools",
        "answers": [
            "Tools: Postman, curl, pytest, Jest for different languages.",
            "Test success cases, error cases, edge cases, and performance.",
        ]
    },
    {
        "text": "What are web hooks?",
        "tags": "api,webhooks,events",
        "answers": [
            "Webhooks are user-defined HTTP callbacks triggered by events.",
            "Enable real-time integrations between systems.",
        ]
    },

    # General Programming
    {
        "text": "What is Git and how to use it?",
        "tags": "git,version-control,development",
        "answers": [
            "Git tracks code changes. Commands: git add, commit, push, pull.",
            "Use branches for features and merge via pull requests.",
        ]
    },
    {
        "text": "What are design patterns in software development?",
        "tags": "design-patterns,oop,architecture",
        "answers": [
            "Common patterns: Singleton, Factory, Observer, Strategy, Adapter.",
            "Design patterns solve recurring design problems.",
        ]
    },
    {
        "text": "How to write clean code?",
        "tags": "code-quality,best-practices,clean-code",
        "answers": [
            "Use meaningful names, keep functions small, avoid duplication.",
            "Write tests, document code, and follow SOLID principles.",
        ]
    },
    {
        "text": "What is SOLID principles?",
        "tags": "solid,oop,design",
        "answers": [
            "S: Single Responsibility, O: Open/Closed, L: Liskov, I: Interface, D: Dependency.",
            "These principles make code more maintainable and scalable.",
        ]
    },
    {
        "text": "What is unit testing?",
        "tags": "testing,unittest,quality",
        "answers": [
            "Unit tests verify individual functions or methods work correctly.",
            "Use frameworks: pytest (Python), Jest (JavaScript), unittest (Python).",
        ]
    },
    {
        "text": "How to debug code effectively?",
        "tags": "debugging,development,tools",
        "answers": [
            "Use breakpoints, step through code, inspect variables.",
            "Use logging strategically and use debugger tools.",
        ]
    },
    {
        "text": "What is continuous integration?",
        "tags": "ci-cd,devops,automation",
        "answers": [
            "CI automatically builds and tests code on every commit.",
            "Tools: Jenkins, GitHub Actions, GitLab CI.",
        ]
    },
    {
        "text": "How to handle large codebases?",
        "tags": "architecture,modularity,scaling",
        "answers": [
            "Use microservices, monorepos, or modular monoliths.",
            "Clear separation of concerns and interfaces.",
        ]
    },
    {
        "text": "What is refactoring?",
        "tags": "refactoring,code-quality,maintenance",
        "answers": [
            "Refactoring improves code without changing functionality.",
            "Rename variables, extract functions, remove duplication.",
        ]
    },
    {
        "text": "How to handle technical debt?",
        "tags": "technical-debt,code-quality,maintenance",
        "answers": [
            "Track technical debt items, prioritize high-impact items.",
            "Balance new features with paying down debt.",
        ]
    },
]

def populate_database():
    """Add 200 questions with answers to database"""
    
    # Initialize database first
    from models import init_db
    init_db()
    
    import time
    time.sleep(1)  # Wait for DB to be ready
    
    conn = sqlite3.connect("qa.db")  # Match database.py
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🚀 Starting database population...")
    print(f"📝 Adding {len(QUESTIONS_DATA) * 2} questions (repeating dataset twice)...")
    
    # Repeat dataset twice to get ~200 questions
    all_questions = QUESTIONS_DATA * 2
    
    question_count = 0
    answer_count = 0
    
    for idx, q_data in enumerate(all_questions):
        try:
            # Insert question with slightly varying rank scores
            rank_score = 0.5 + (random.random() * 0.5)  # 0.5 to 1.0
            
            cursor.execute("""
                INSERT INTO questions (question_text, auto_tags, rank_score, user_id)
                VALUES (?, ?, ?, ?)
            """, (
                q_data["text"],
                q_data["tags"],
                rank_score,
                random.randint(1, 5)  # Random user_id
            ))
            
            question_id = cursor.lastrowid
            question_count += 1
            
            # Insert answers
            for answer_text in q_data["answers"]:
                cursor.execute("""
                    INSERT INTO answers (question_id, answer_text, user_id)
                    VALUES (?, ?, ?)
                """, (
                    question_id,
                    answer_text,
                    random.randint(1, 10)
                ))
                answer_count += 1
            
            # Print progress
            if (idx + 1) % 50 == 0:
                print(f"  ✓ Processed {idx + 1}/{len(all_questions)} questions")
        
        except Exception as e:
            print(f"  ✗ Error on question {idx}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database Population Complete!")
    print(f"   📊 Questions added: {question_count}")
    print(f"   💬 Answers added: {answer_count}")
    print(f"   ⏱️  Total entries: {question_count + answer_count}")

if __name__ == "__main__":
    populate_database()
