function graph_maker_histogram(filename, tle, x_axis, y_axis)
  
 clc;
 fileID = fopen(filename,'r');
 
  formatSpec = '%f';
 
 results = fscanf(fileID,formatSpec);
  histogram(results)
 
 title(tle);
 xlabel(x_axis);
 ylabel(y_axis);
 
 [file_save, ] = strtok(filename, '.'); % Removes the file extension
 
 file_save = [file_save, '.jpg'];
 
 saveas(figure(1), file_save); % Saves as a jpg

end