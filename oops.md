Object-Oriented Programming (OOP) is a programming paradigm centered around objects that combine data (fields/attributes) and behavior (methods) rather than just functions and logic. [1, 2] 
------------------------------
## Core Building Blocks

* Class: A user-defined blueprint or template that defines the properties and methods common to a type of object. It does not occupy memory on its own. (Analogy: An architectural blueprint for a house) [1, 2, 3] 
* Object: A concrete instance of a class that holds actual values and occupies memory. (Analogy: The actual built house) [1, 2, 3] 
* Constructor: A special method automatically called when an object is created, used to initialize its properties. [4] 

------------------------------
## The Four Pillars of OOP

* Encapsulation: Bundling data and the methods that operate on that data inside a class while hiding internal states from the outside world using access modifiers (like private). Access is typically managed via public getter and setter methods to prevent invalid states. [4, 5, 6] 
* Abstraction: Hiding complex internal implementation details and exposing only the essential features to the user. It is commonly achieved using abstract classes and interfaces. (Analogy: Using a TV remote without needing to understand internal circuit boards) [1, 4, 7] 
* Inheritance: A mechanism where a child/subclass acquires the fields and methods of a parent/superclass, establishing an "is-a" relationship to promote code reusability. [4, 7, 8] 
* Polymorphism: The ability of a single method, operator, or object to take "many forms". It allows different classes to share the same method name with unique implementations (achieved via method overloading and method overriding). [2, 9] 

------------------------------
## Supporting & Relationship Concepts

* Association: A general relationship showing how separate classes interact and communicate with each other.
* Aggregation: A specialized "has-a" relationship where one class contains a reference to another, but both can exist independently.
* Composition: A stricter "has-a" relationship where the child object cannot exist independently of the parent object.
* Interface: A contract that defines a set of methods a class must implement without providing the body code. [3, 4] 

------------------------------
## Advantages vs. Limitations

* Advantages: Improved code reusability, modularity, easier maintenance, scalability, and intuitive real-world modeling. [2, 4] 
* Limitations: Steeper learning curve for beginners, extra structural overhead for small programs, and higher memory consumption. [2, 4] 

For a deeper dive into code syntax and implementations, you can explore the [GeeksforGeeks Java OOP Guide](https://www.geeksforgeeks.org/java/object-oriented-programming-oops-concept-in-java/). [4] 
If you'd like, let me know:

