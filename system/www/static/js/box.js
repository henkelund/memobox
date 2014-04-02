(function (exports, ng, $, console) {
    'use strict';

    /**
     * @var Object box
     */
    var box = ng.module('box', ['ngResource', 'ui.router', 'infinite-scroll', 'ngSanitize']);
    exports.box = box;
	
	box.directive('myMainDirective', function() {
	  return function(scope, element, attrs) {
	      $("#dateHolder").sticky({ topSpacing: 0, center:true, className:"hey" });
	  };
	})

	box.directive('myRepeatDirective', function() {
	  return function(scope, element, attrs) {
	    if (scope.$last){
	      //scope.$emit('LastElem');
	    }

	    scope.$watch('thing', function(){
	    });
	  };
	})
	
	box.controller('DemoController', function($scope, Reddit) {
	  $scope.reddit = new Reddit($scope);
	  //$scope.fileservice = new FileService($scope);
	  $scope.items = [];
	  $scope.render = function(e) {
	    return $(e).html();
	  }
    	  
	});
	
	// Reddit constructor function to encapsulate HTTP and pagination logic
	box.factory('Reddit', function($http) {
	  var Reddit = function($scope) {
	  	this.me = $scope;
	    this.images = [];
	    this.busy = false;
	    this.after = 1;
	    this.viewMonth = null;
	    this.viewYear = null; 
		this.monthArr = "Alert";
		this.device = -1; 
	  };
	  
	  Reddit.prototype.showPicture = function(file) {
		$.ajax({
		    url : "/files/details?id="+file,
			async: false,
			context: this,
		    success : function(result){
				var ts = new Date(null);
				ts.setTime(result.timestamp*1000);
		
				if(result.type == "video") {
					$("#modalVideo > source").attr("src", result.abspath.replace("/backupbox/data/devices/", "/static/devices/")+"/"+result.name)
					$("#modalVideo").show();
					$("#modalImage").hide();
				} else {
					$("#modalVideo").hide();
					$("#modalImage").show();
					$("#modalDownload").attr("href", "/files/stream/"+result._id+"/"+result.name);
					$("#modalImage").attr("src", "/static/images/"+result.thumbnail);
				}
		
		        $('#filesDetailModal').modal('show');				
		    }
		});	  	
  	
	  	//var f = new FileService();
	  	//f.loadDetails(file);	  	
	  }
	  
	  Reddit.prototype.nextPage = function(_device) {
	    if (this.busy) return;
	    this.busy = true;	
	    var changedDevice = false; 
		if(_device != null) {
			if(this.device != _device) {
				changedDevice = true;
				this.after = 1; 
				$(".device").removeClass("selectedDevice");
				$("#"+_device).addClass("selectedDevice");
			}
			this.device = _device; 

			$.ajax({
			    url : "/files/calendar?device="+_device,
				async: false,
				context: this,
			    success : function(result){
					
			    }
			});
		}
	
		$.ajax({
		    url : "/files?after="+this.after+"&device="+this.device,
			async: false,
			context: this,
		    success : function(result){
		    	if(changedDevice == true) {
					this.me.items = [];
				}

			    for(var i = 0; i < result.files.length; i++) {
			      var type_content = ""; 
			      
			      if(result.files[i].type == "video" && result.files[i].value != null) {
			      	  var video_length = result.files[i].value.split(" ")
			      	  var suffix = "ms"; 
			      	  
			      	  for (var ind = 0; ind < video_length.length; ++ind) {
			      	  	if(video_length[ind].indexOf(suffix, video_length[ind].length - suffix.length) == -1)
							type_content += video_length[ind]+" ";
					  }
			      }			      
			      this.me.items.push({background:result.files[i].thumbnail, id:result.files[i].file, created_at:result.files[i].created_at, type:result.files[i].type, type_content:type_content});
			    }			    

		        this.after = this.after + 1;
		        this.busy = false;		        
		    }
		});
	  };
	
	  return Reddit;
	});	

    /**
     * Configure the box app
     */
    box.config(function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise('/');

        $stateProvider
            .state('devices', {
                url: '/devices',
                controller: 'DevicesCtrl',
                templateUrl: '/templates/devices.html'
            })
            .state('files', {
                url: '/',
                controller: 'FilesCtrl',
                templateUrl: '/templates/files.html'
            })
    });

    /**
     * Run the box app
     */
    box.run(function ($window) {

        ng.element($window).bind('scroll', function () {
            var winHeight = $($window).height();
            $('.preview.image').each(function () {
                var rect = this.getBoundingClientRect(),
                    el = $(this),
                    pos,
                    percent;
                if (rect.bottom >= 0 && rect.top <= winHeight) {
                    pos = rect.top / (winHeight - el.height());
                    percent = Math.round(Math.min(100, Math.max(0,
                                pos * 100)));
                    el.css('backgroundPosition', '50% ' + percent + '%');
                }
            });
        });
    });

    /**
     * File service
     */
    box.factory('FileService', function ($resource, $window, $q) {

        /**
         *
         */
        var FileService = function () {
            this.filesResource = $resource('/files');
            this.filterResource = $resource('/files/filters');
            this.detailsResource = $resource('/files/details');
            this.deviceResource = $resource('/files/devices');
            this.calendarResource = $resource('/files/calendar');
            this.calendar = [];
            this.devices = [];
            this.files = [];
            this.filters = [];
            this.details = [];
        };
        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadFilesSuccess: function (resource) {
                this.files = resource.files;
                console.log(resource.sql);
            },

            /**
             * Successful filters load callback
             */
            loadFiltersSuccess: function (data) {
                this.filters = data.filters;
            },

            /**
             * Successful filters load callback
             */
            loadCalendarSuccess: function (data) {
                this.calendar = data;
            },

            /**
             * Successful filters load callback
             */
            loadDevicesSuccess: function (data) {
                this.devices = data.devices;
            },


            /**
             * Successful filters load callback
             */
            loadDetailsSuccess: function (data) {
                if (data['_id'] !== undefined) {
                    this.details[data['_id']] = data;
                }
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                console.log(data);
            },

            /**
             * Load files passing 'filter'
             */
            loadFiles: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key

                if ($window.devicePixelRatio && $window.devicePixelRatio > 1) {
                    args.retina = 1;
                }

                if (typeof filter === 'object') {
                    for (fk in filter) {
                        if (filter.hasOwnProperty(fk) && filter[fk].length) {
                            args[fk] = filter[fk].join(',');
                        }
                    }
                }

                this.filesResource.get(
                    args,
                    function (data) {
                        that.loadFilesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },


            /**
             * Load available calendar
             */
            loadCalendar: function () {
                this.calendarResource.get(
                    {},
                    this.loadCalendarSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load available devices
             */
            loadDevices: function () {
                this.deviceResource.get(
                    {},
                    this.loadDevicesSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },
            
            /**
             * Load available filters
             */
            loadFilters: function () {
                this.filterResource.get(
                    {},
                    this.loadFiltersSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load file by id
             */
            loadDetails: function (id) {
                var that = this,
                    deferred = $q.defer(),
                    resource;

                if (this.details[id] !== undefined) {
                    deferred.resolve();
                } else {
                    resource = this.detailsResource.get(
                        {id: id},
                        function (data) {
                            that.loadDetailsSuccess(data);
                            deferred.resolve();
                        },
                        function (data) {
                            that.loadError(data);
                            deferred.resolve();
                        }
                    );
                }

                return deferred.promise;
            },

            /**
             * Get laoded details
             */
            getDetails: function (id) {
                return this.details[id] || false;
            }
        };

        return new FileService();
    });

    /**
     * Device service
     */
    box.factory('DeviceService', function ($resource, $window, $q) {

        /**
         *
         */
        var DeviceService = function () {
            this.devicesResource = $resource('/files/devices');
            this.devices = [];
        };
        DeivceService.prototype = {

            /**
             * Successful devices load callback
             */
            loadDevicesSuccess: function (resource) {
                this.devices = resource.devices;
                console.log(resource.sql);
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                console.log(data);
            },

            /**
             * Load devices passing 'devices'
             */
            loadDevices: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key


                this.devicesResource.get(
                    args,
                    function (data) {
                        that.loadDevicesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },

        };

        return new DeviceService();
    });


    /**
     * File thumbnail directive
     */
    box.directive('fileThumbnail', function ($window) {
        return {
            restrict: 'A',
            link: function (scope, element) {
                var el = ng.element(element),
                    file = scope.file,
                    imgUrl = '/static/images/';
                if (file.thumbnail) {
                    el.addClass('image')
                        .css('backgroundImage',
                                'url(' + imgUrl + file.thumbnail + ')')
			.find('img').attr('src', imgUrl + file.icon_small).hide();
			$($window).scroll(); // provoke background re-positioning
                } else {
                    el.addClass('icon')
                        .find('img').attr('src', imgUrl + file.icon_large);
                }
            }
        };
    });

    /**
     * File tooltip directive
     */
    box.directive('fileTooltip', function () {
        return {
            restrict: 'A',
            link: function (scope, element) {
                var file = scope.file;
                $(element).tooltip({
                    title: file.devpath + '/' + file.name+file.extension,
                    placement: 'top'
                });
            }
        };
    });

    /**
     * Available filters filter
     */
    box.filter('availableFilters', function () {
        return function (filters, scope) {
            if (scope.FilesCtrl === undefined) {
                return filters;
            }
            return $.grep(filters, function (item) {
                return scope.FilesCtrl.isFilterAvailable(item);
            });
        };
    });

    /**
     * Active filters filter
     */
    box.filter('activeFilters', function () {
        return function (filters, scope) {
            if (scope.FilesCtrl === undefined) {
                return filters;
            }
            return $.grep(filters, function (item) {
                return scope.FilesCtrl.isFilterActive(item);
            });
        };
    });

    /**
     * Active filter options filter
     */
    box.filter('activeFilterOptions', function () {
        return function (options, filter, scope) {
            var value,
                result = {};
            if (scope.FilesCtrl === undefined) {
                return options;
            }
            for (value in options) {
                if (options.hasOwnProperty(value) &&
                        scope.FilesCtrl.isFilterActive(filter, value)) {
                    result[value] = options[value];
                }
            }
            return result;
        };
    });

    /**
     * File extension trim filter
     */
    box.filter('trimFileExtension', function () {
        return function (fileName) {
            var parts = fileName.split('.');
            if (parts.length >= 2) {
                parts.pop();
            }
            return parts.join('.');
        };
    });

    /**
     * Files controller
     */
    box.controller('FilesCtrl', function ($scope, $location, FileService) {

        var that = this;
        this.fileService = FileService.loadFilters().loadFiles().loadDevices();
        this.filterState = {};
        this.isFilterPending = false;
        $('#filesDetailModal').modal({show: false})
                .on('hide.bs.modal', function () {
            $location.path('/');
            $scope.$apply();
        });

        /**
         * Check if a given filter - or option - is active
         */
        this.isFilterActive = function (filter, value) {
            var state;
            if (filter === undefined) {
                for (state in that.filterState) {
                    if (that.filterState.hasOwnProperty(state) &&
                            that.filterState[state].length > 0) {
                        return true;
                    }
                }
                return false;
            }
            state = that.filterState[filter.param];
            return (state !== undefined) &&
                        (state.length > 0) &&
                        (value === undefined ||
                            state.indexOf(value) >= 0);
        };

        /**
         * Check if a given filter - or option - is available
         */
        this.isFilterAvailable = function (filter, value) {
            var i,
                val;

            if (filter === undefined) {
                filter = that.fileService.filters;
            } else {
                filter = [filter];
            }

            if (value === undefined) {
                for (i = 0; i < filter.length; ++i) {
                    for (val in filter[i].options) {
                        if (filter[i].options.hasOwnProperty(val) &&
                                !that.isFilterActive(filter[i], val)) {
                            return true;
                        }
                    }
                }
                return false;
            }

            for (i = 0; i < filter.length; ++i) {
                if (!that.isFilterActive(filter[i], value)) {
                    return true;
                }
            }
            return false;
        }

        /**
         * Toggle a given filter option
         */
        this.filterClicked = function (filter, value) {
            var i, state = that.filterState[filter.param];
            if (state === undefined) {
                state = that.filterState[filter.param] = [];
            }
            i = state.indexOf(value);
            if (i >= 0) {
                state.splice(i, 1);
            } else {
                if (filter.multi === undefined || !filter.multi) {
                    state = [];
                }
                state.push(value);
            }
            that.isFilterPending = true;
            that.fileService.loadFiles(that.filterState, function () {
                that.isFilterPending = false;
            });
        };

        $scope.FilesCtrl = this;
        return this;
    });

}(window, angular, jQuery, console || {log: function () { 'use strict'; return; }}));

