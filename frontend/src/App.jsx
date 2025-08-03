import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConversionProvider } from './context/ConversionContext';
import { ThemeProvider } from './context/ThemeContext';
import Home from './components/pages/Home';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';

function App() {
  return (
    <ThemeProvider>
      <ConversionProvider>
        <Router>
          <div className="min-h-screen flex flex-col bg-gradient-to-br from-gradient-1-light via-gradient-2-light to-gradient-3-light dark:from-gradient-1-dark dark:via-gradient-2-dark dark:to-gradient-3-dark transition-colors duration-300">
            <Header />
            <main className="flex-grow">
              <Routes>
                <Route path="/" element={<Home />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </Router>
      </ConversionProvider>
    </ThemeProvider>
  );
}

export default App;