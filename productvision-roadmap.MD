# Product Vision

Our idea is to use LLMs to interpret a students syllabus, providing sources through lines and page numbers. As students, the first week of class is used by professors for going over the syllabus. Most syllabus are long and tedious to read, so many students either do not read or understand the syllabus leading to surprises later in the course. The product will give students the ability to sign up and upload syllabi and other class documents through a user interface, and can then “chat” with the LLM to better understand and dissect the documents and course policies. 

# Product Backlog

- Ability to sign up for an account  
- Ability to log into an account  
- Ability to upload syllabus as a file  
- Ability to view list of uploaded syllabi by the user  
- Ability to view if attendance is required for a class  
- Ability to upload syllabus as text  
- Ability for students to ask questions in a text box  
- Implement RAG with AI model to get accurate responses about the syllabus  
- Ability to view the grade distribution of a class  
- Ability to edit user information  
- Ability to delete syllabi  
- Ability to upload other documents relevant to the class (project descriptions, etc.)  
- Ability to see exams in a calendar format  
- Chatbot to highlight where information is found in the syllabus  
- Show warnings whenever a question is not covered by the documents  
- Database to store all syllabi and login information  
- Graphical User Interface  
- Receive reminders for upcoming deadlines/exams  
- Ability to automatically see commonly asked questions with answers  
- Ability to reset password  

---

# Product Roadmap

## Sprint 1: Foundation and Core Functionality

- Set up Flask and implement authentication with Supabase  
  - **Stories:**  
    - Ability to sign up for an account  
    - Ability to log into an account  
    - Database to store all syllabi and login information  

- Create syllabus upload functionality  
  - **Stories:**  
    - Ability to upload syllabus as a file  
    - Ability to upload syllabus as text  

- Develop initial dashboard  
  - **Story:** Ability to view list of uploaded syllabi by the user  

- Set up basic Graphical User Interface (GUI) with Tailwind CSS  
  - **Story:** Graphical User Interface  

- Set up user settings where they can change user information  
  - **Stories:** Ability to edit user information  

---

## Sprint 2: Core Chatbot and Document Management

- Develop chatbot interface and connect to OpenAI’s API  
  - **Story:** Ability for students to ask questions in a text box  

- Implement RAG for document analysis  
  - **Story:** Implement RAG with AI model to get accurate responses about the syllabus  

- Enable chatbot to provide highlighted, source-backed answers  
  - **Story:** Chatbot to highlight where information is found in the syllabus  

- Implement detection of attendance policies and grade distributions  
  - **Stories:**  
    - Ability to view if attendance is required for a class  
    - Ability to view the grade distribution of a class  

- Add document management features (edit, delete syllabi, upload other documents)  
  - **Stories:**  
    - Ability to delete syllabi  
    - Ability to upload other documents relevant to the class  

- Incorporate warnings when user questions are not covered by documents  
  - **Story:** Show warnings whenever a question is not covered by the documents  

---

## Sprint 3: Calendar Integration, Reminders, and FAQs

- Build calendar view for exams with date extraction from syllabi  
  - **Story:** Ability to see exams in a calendar format  

- Implement automated reminders for upcoming deadlines and exams  
  - **Story:** Receive reminders for upcoming deadlines/exams  

- Add functionality to automatically display commonly asked questions with answers  
  - **Story:** Ability to automatically see commonly asked questions with answers  

- Conduct final testing, bug fixes, and UI/UX enhancements  

- Prepare for deployment and gather user feedback for continuous improvement  
