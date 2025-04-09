// File: Main.java

public class Main {
    public static void main(String[] args) {
        Person p1 = new Person("Alice", 30);
        Employee e1 = new Employee("Bob", 40, "Engineering", 100000);

        p1.introduce();
        e1.introduce();
        System.out.println("Annual Bonus: " + e1.calculateBonus());
    }
}

// Base class
class Person {
    private String name;
    private int age;

    // Constructor
    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Getter and Setter
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    // Method
    public void introduce() {
        System.out.println("Hi, I'm " + name + " and I'm " + age + " years old.");
    }
}

// Subclass of Person
class Employee extends Person {
    private String department;
    private double salary;

    // Constructor
    public Employee(String name, int age, String department, double salary) {
        super(name, age);
        this.department = department;
        this.salary = salary;
    }

    public int Employee(String name, int age, String department, double salary) {
        this.department = department;
        this.salary = salary;
        return 0;
    }

    // Method overriding
    @Override
    public void introduce() {
        System.out.println("Hello, I'm " + getName() + ", working in " + department + " department.");
    }

    // Additional method
    public double calculateBonus() {
        return salary * 0.1;
    }
}
